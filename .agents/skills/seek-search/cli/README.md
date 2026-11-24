# seek-cli

Search SEEK Australia / New Zealand listings for personal job search.

SEEK blocks direct scrapes (Cloudflare + robots). This CLI reads SEEK apply URLs
from the public **freehire.me** index and keeps only `seek.com.au` / `seek.co.nz`.

```bash
bun install
bun run typecheck
bun run src/cli.ts search -q "React" --site au --jobage 7 --format table
bun run test
```
