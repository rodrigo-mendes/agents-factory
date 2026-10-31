# GraphQL and rate limits (gh 2.103.x)

Back to [SKILL.md](../SKILL.md). Sources fetched 2026-10-29.

## gh api basics

```bash
gh api graphql -F number=7 -f owner=my-org -f query='query($owner:String!,$number:Int!){...}'
gh api repos/my-org/repo/issues/42 --jq .id
gh api -i repos/my-org/repo/issues/42        # include response headers
gh api --paginate --slurp "repos/my-org/repo/issues/42/comments?per_page=100"
```

- `-f` sends a string, `-F` types the value (numbers, booleans, files). Source: https://cli.github.com/manual/gh_api
- `--paginate` on GraphQL needs a `$endCursor: String` variable and `pageInfo { hasNextPage endCursor }`; `--slurp` wraps all pages in one array. Source: https://cli.github.com/manual/gh_api
- PowerShell: quote arguments that contain `{owner}` or `{repo}` placeholders (see [Windows notes](./non-interactive-and-windows.md#windows-notes)).
- `jq` need not be installed for `--jq`. Source: https://cli.github.com/manual/gh_help_formatting

## Query limits

| Limit | Value | Source |
|---|---|---|
| Connection size | `first` or `last` between 1 and 100 | https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api |
| Nodes per call | at most 500,000 | same page |
| Call timeout | 10 seconds; a timeout returns 502 or 504 and deducts extra points | same page |
| Mutation cost | 5 points | https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api |
| Secondary limits | 100 concurrent requests; 900 points per minute per REST endpoint; 2,000 per minute GraphQL | same page |
| Content creation | about 80 requests per minute, 500 per hour | same page |

## Monitoring headroom

```bash
gh api graphql -f query='{ rateLimit { limit remaining used resetAt cost } }'
gh api -i repos/my-org/repo/issues/42 | head -n 20     # x-ratelimit-remaining, -reset, -used, -resource
```

- GraphQL primary-limit exhaustion still returns HTTP 200 with remaining 0; REST returns 403 or 429. Check `remaining`, not only the status. Source: https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api
- Conditional requests with `If-None-Match` that return 304 do not count against the primary limit. Source: https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api
- The `gh api rate_limit` endpoint was not read; treat its use as (medium confidence).

## Backoff algorithm

1. Make writes serially; wait at least one second after each POST, PATCH, PUT or DELETE.
2. On a secondary limit: if `retry-after` is present, wait that many seconds.
3. Else if `x-ratelimit-remaining` is 0, wait until the time in `x-ratelimit-reset`.
4. Else wait at least one minute; on repeated failures use exponential backoff, then stop and report.
5. Never keep sending while limited: the docs warn it "may result in the banning of your integration".

Sources: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api , https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api

Headers are visible only with `gh api -i`; header parsing is the precise path, while matching the stderr text "rate limit" is (unverified) and only a fallback.

## Batching reads

- Batch reads with GraphQL connections of up to 100 nodes per page rather than one `gh` process per item. Source: https://docs.github.com/en/graphql/overview/rate-limits-and-query-limits-for-the-graphql-api
- GraphQL aliases let one request carry several mutations or lookups; `gh api graphql` is the path for bulk sync. Source: https://docs.github.com/en/graphql/reference/projects
- Mutations cost 5 points each, so budget writes against the per-minute points limit above.

## Primary limits by credential

| Credential | Limit per hour |
|---|---|
| PAT or user token | 5,000 points or requests |
| GitHub App installation | 5,000 to 12,500 (Enterprise Cloud REST 15,000; GraphQL 10,000) |
| `GITHUB_TOKEN` | 1,000 per repository |

Source: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
