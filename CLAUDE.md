# ⛔ HARD RULE — THE REPOSITORY IS NOT TO BE TOUCHED AT THE FILE LEVEL

**This is a hard set. It is not a preference, and it is not negotiable.**

Never delete, move, overwrite or "clean up" anything inside `.git/`. Never run a
bulk delete over this folder — no `find … -delete`, no `find … -exec rm`, no
duplicate-file sweep, no "free up space" script. A guard hook
(`~/.claude/hooks/protect-git.sh`) blocks these and will refuse the command; do
not try to work around it, and do not rewrite a command to slip past it. If you
believe something under `.git/` genuinely must change, stop and ask Rohit.

Change this repository the normal way — `git add`, `git commit`, `git checkout`,
`git restore`, `git reset`. Those are safe and always allowed.

## Why this rule exists

On **27 July 2026 at 02:27**, a Claude Code session ran a "delete duplicate
files" sweep across `~/Desktop`. It hashed every file, kept the alphabetically
first copy of each hash, and `rm -f`'d every other copy.

`.git/HEAD`, `.git/description`, `.git/info/exclude` and the 14
`.git/hooks/*.sample` files are **byte-identical in every git repository on
earth**. The sweep saw them as duplicates and deleted them.

The result: **three repositories destroyed** — FamilyBook, JobRadar and RehabApp
all lost `.git/HEAD`, so `git` refused every command with *"not a git
repository"*. RehabApp additionally lost **252 source files** (its `dist/` copy
sorted first, so the originals were deleted). FamilyBook lost three web fonts.

Nothing warned anyone. It was found four days later, by accident, while starting
unrelated work. Everything was recoverable only because the commits themselves
had been pushed to GitHub.

## If git says "not a git repository"

Check `.git/HEAD` before assuming the worst — it is one line and it is probably
just missing:

```bash
printf 'ref: refs/heads/main\n' > .git/HEAD
```

(You will have to run that yourself; the guard blocks Claude from writing into
`.git/`, deliberately.) Then `git fsck --full` and `git status` to confirm.

