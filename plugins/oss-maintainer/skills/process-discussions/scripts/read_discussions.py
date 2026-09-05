#!/usr/bin/env python3
"""Read complete Discussion queues and threads with independent connection pagination.

read_discussions.py queue --repo OWNER/NAME --category ID
read_discussions.py thread --repo OWNER/NAME --number N

Uses authenticated `gh api graphql` (read-only). JSON always includes `complete`;
exit 1 means a partial read, never a basis for a final facilitation decision.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

QUEUE = '''query($owner: String!, $name: String!, $category: ID!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    discussions(first: 50, after: $cursor, categoryId: $category,
      orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes { id number title createdAt closed author { login } comments { totalCount } }
      pageInfo { hasNextPage endCursor }
    }
  }
}'''
THREAD = '''query($owner: String!, $name: String!, $number: Int!) {
  repository(owner: $owner, name: $name) {
    discussion(number: $number) { id number title body author { login } createdAt closed }
  }
}'''
COMMENTS = '''query($id: ID!, $cursor: String) {
  node(id: $id) { ... on Discussion {
    comments(first: 100, after: $cursor) {
      nodes { id body author { login } createdAt }
      pageInfo { hasNextPage endCursor }
    }
  } }
}'''
REPLIES = '''query($id: ID!, $cursor: String) {
  node(id: $id) { ... on DiscussionComment {
    replies(first: 50, after: $cursor) {
      nodes { id body author { login } createdAt }
      pageInfo { hasNextPage endCursor }
    }
  } }
}'''


class ReadError(Exception):
    pass


def graphql(query: str, variables: dict) -> dict:
    try:
        proc = subprocess.run(['gh', 'api', 'graphql', '--input', '-'],
                              input=json.dumps({'query': query, 'variables': variables}),
                              capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReadError(f'GraphQL request unavailable: {exc}') from exc
    if proc.returncode:
        raise ReadError(proc.stderr.strip() or f'gh exited {proc.returncode}')
    try:
        payload = json.loads(proc.stdout)
    except ValueError as exc:
        raise ReadError('GraphQL returned invalid JSON') from exc
    if payload.get('errors'):
        raise ReadError('; '.join(error.get('message', 'GraphQL error') for error in payload['errors']))
    if not isinstance(payload.get('data'), dict):
        raise ReadError('GraphQL returned no data')
    return payload['data']


def descend(data: dict, *path: str):
    for key in path:
        if not isinstance(data, dict) or key not in data or data[key] is None:
            raise ReadError(f'Missing GraphQL result: {".".join(path)}')
        data = data[key]
    return data


def pages(api, query: str, variables: dict, path: tuple):
    cursor = None
    seen = set()
    while True:
        connection = descend(api(query, dict(variables, cursor=cursor)), *path)
        nodes = descend(connection, 'nodes')
        info = descend(connection, 'pageInfo')
        if not isinstance(nodes, list) or not isinstance(info, dict) or type(info.get('hasNextPage')) is not bool:
            raise ReadError('Invalid pagination response')
        for node in nodes:
            if not isinstance(node, dict):
                raise ReadError('Unavailable node in connection')
            yield node
        if not info['hasNextPage']:
            return
        cursor = info.get('endCursor')
        if not isinstance(cursor, str) or not cursor or cursor in seen:
            raise ReadError('Pagination stopped: missing or repeated cursor')
        seen.add(cursor)


def read_queue(api, variables: dict, result: dict) -> None:
    result['threads'] = []
    for thread in pages(api, QUEUE, variables, ('repository', 'discussions')):
        if thread.get('closed') is False:
            result['threads'].append(thread)
        elif thread.get('closed') is not True:
            raise ReadError('Discussion is missing its closed state')


def read_thread(api, variables: dict, result: dict) -> None:
    thread = descend(api(THREAD, variables), 'repository', 'discussion')
    result['thread'] = thread
    thread['comments'] = []
    for comment in pages(api, COMMENTS, {'id': thread['id']}, ('node', 'comments')):
        thread['comments'].append(comment)
        comment['replies'] = []
        for reply in pages(api, REPLIES, {'id': comment['id']}, ('node', 'replies')):
            comment['replies'].append(reply)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['queue', 'thread'])
    parser.add_argument('--repo', required=True)
    parser.add_argument('--category')
    parser.add_argument('--number', type=int)
    args = parser.parse_args(argv)
    repo = args.repo.split('/')
    if len(repo) != 2 or not all(repo):
        parser.error('--repo must be OWNER/NAME')
    if args.command == 'queue' and not args.category:
        parser.error('queue requires --category')
    if args.command == 'thread' and (args.number is None or args.number < 1):
        parser.error('thread requires a positive --number')
    variables = {'owner': repo[0], 'name': repo[1]}
    result = {'complete': False}
    try:
        if args.command == 'queue':
            read_queue(graphql, dict(variables, category=args.category), result)
        else:
            read_thread(graphql, dict(variables, number=args.number), result)
        result['complete'] = True
    except (ReadError, KeyError, TypeError) as exc:
        result['error'] = str(exc)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result['complete'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
