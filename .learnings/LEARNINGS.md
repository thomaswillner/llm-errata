# Project learnings

## [LRN-20260813-001] best_practice

**Logged**: 2026-08-13T02:28:16+02:00
**Priority**: high
**Status**: resolved
**Area**: docs

### Summary

Verify every pinned GitHub blob link against the exact commit before publishing outreach.

### Details

The targeted implementation draft initially linked to `IMPLEMENTATION_CALL.md`
at the corrected frozen commit, but that path does not exist in the tree.
Pre-publication `git cat-file -e <commit>:<path>` validation caught the defect
before any external comment was written. Full link validation then found the
same dead path in an older ignored draft, showing that publication artifacts
must be checked even when they are not tracked.

### Suggested Action

For every external comment containing a pinned blob URL, extract its commit and
path, verify the object with `git cat-file -e`, then confirm public HTTP
resolution before posting.

### Metadata

- Source: error
- Related Files: `.scratch/g2-publication/issue-5-targeted-implementation.md`
- Tags: github, outreach, immutable-target, link-validation
- Pattern-Key: publication.verify_pinned_blob_before_post
- Recurrence-Count: 1
- First-Seen: 2026-08-13
- Last-Seen: 2026-08-13

### Resolution

- **Resolved**: 2026-08-13T02:28:16+02:00
- **Commit/PR**: agent/g2-publication publication follow-up
- **Notes**: Replaced nonexistent blob URLs with Issue #5 links and verified all remaining pinned paths before publication.

---
