"""Offline multi-page GraphQL fixtures and CLI-recipe regression checks."""
import importlib.util
import json
import shutil
import subprocess

import pytest

from tests.conftest import PLUGIN

SCRIPT = PLUGIN / 'skills/process-discussions/scripts/read_discussions.py'
spec = importlib.util.spec_from_file_location('read_discussions', SCRIPT)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def connection(nodes, cursor=None):
    return {'nodes': nodes, 'pageInfo': {'hasNextPage': cursor is not None, 'endCursor': cursor}}


def test_queue_does_not_stop_after_fifty_closed_threads():
    calls = []
    def api(query, variables):
        calls.append(variables['cursor'])
        if variables['cursor'] is None:
            page = connection([{'number': n, 'closed': True} for n in range(1, 51)], 'next')
        else:
            assert variables['cursor'] == 'next'
            page = connection([{'number': 51, 'closed': False}])
        return {'repository': {'discussions': page}}
    result = {}
    reader.read_queue(api, {'owner': 'x', 'name': 'y', 'category': 'c'}, result)
    assert calls == [None, 'next']
    assert result['threads'] == [{'number': 51, 'closed': False}]


def test_comments_and_nested_replies_have_independent_cursors():
    calls = []
    def api(query, variables):
        calls.append((query, variables))
        if query == reader.THREAD:
            return {'repository': {'discussion': {'id': 'discussion', 'body': 'context'}}}
        if query == reader.COMMENTS:
            nodes = [{'id': f'c{n}'} for n in range(1, 101)] if variables['cursor'] is None else [{'id': 'c101', 'body': 'last decision'}]
            return {'node': {'comments': connection(nodes, 'comments-next' if variables['cursor'] is None else None)}}
        assert query == reader.REPLIES
        if variables['id'] in ('c1', 'c101'):
            if variables['cursor'] is None:
                page = connection([{'id': f'r{n}'} for n in range(50)], 'replies-next')
            else:
                assert variables['cursor'] == 'replies-next'
                page = connection([{'id': 'r50', 'body': 'last reply'}])
        else:
            assert variables['cursor'] is None
            page = connection([])
        return {'node': {'replies': page}}
    result = {}
    reader.read_thread(api, {'owner': 'x', 'name': 'y', 'number': 1}, result)
    comments = result['thread']['comments']
    assert len(comments) == 101 and comments[-1]['body'] == 'last decision'
    assert len(comments[0]['replies']) == len(comments[-1]['replies']) == 51
    assert comments[-1]['replies'][-1]['body'] == 'last reply'


def test_rate_limit_returns_partial_context_without_complete(monkeypatch, capsys):
    def api(query, variables):
        if variables['cursor']:
            raise reader.ReadError('rate limit exceeded')
        return {'repository': {'discussions': connection([{'number': 1, 'closed': False}], 'next')}}
    monkeypatch.setattr(reader, 'graphql', api)
    assert reader.main(['queue', '--repo', 'x/y', '--category', 'c']) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload['complete'] is False
    assert len(payload['threads']) == 1
    assert 'rate limit' in payload['error']


def test_repeated_cursor_is_an_incomplete_read():
    def api(query, variables):
        return {'repository': {'discussions': connection([], 'same')}}
    with pytest.raises(reader.ReadError, match='repeated cursor'):
        reader.read_queue(api, {}, {})


def test_graphql_errors_do_not_count_as_complete_data(monkeypatch):
    def run(*args, **kwargs):
        assert args[0] == ['gh', 'api', 'graphql', '--input', '-']
        assert json.loads(kwargs['input'])['variables']['name'] == 'repo'
        return subprocess.CompletedProcess(args[0], 0, json.dumps({'data': {}, 'errors': [{'message': 'denied'}]}), '')
    monkeypatch.setattr(reader.subprocess, 'run', run)
    with pytest.raises(reader.ReadError, match='denied'):
        reader.graphql(reader.QUEUE, {'name': 'repo'})


def test_precedent_search_recipe_has_no_invalid_all_state():
    paths = (PLUGIN / 'skills').rglob('*.md')
    recipes = [line for path in paths for line in path.read_text().splitlines() if 'gh search issues ' in line]
    assert recipes
    assert all('--state all' not in line for line in recipes)
    if shutil.which('gh'):
        help_result = subprocess.run(['gh', 'search', 'issues', '--help'], capture_output=True, text=True)
        assert help_result.returncode == 0
        assert '{open|closed}' in help_result.stdout
