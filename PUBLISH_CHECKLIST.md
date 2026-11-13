# Publish checklist

Ordered checklist for flipping the `quangtienhn/ha-tts-broadcast` repository from
private to public safely. Do these in order; do not skip the secrets review.

## Before going public

1. **Review the secrets/PII scan result.**
   - Confirm no tokens, passwords, emails, IPs, internal URLs, or real household
     identifiers exist in the working tree or git history.
   - The scan found no secrets in the tree or history. If anything is found in
     history, do NOT rewrite history or force-push; decide with the repo owner
     whether to keep the history or start a fresh squashed repository.
2. **Decide the license holder name** used in `LICENSE` / README (the GitHub
   account `quangtienhn` or a legal entity).
3. **Screenshots** (see `docs/images/README.md`): the dashboard card, Assist
   pipeline setup and Voice phrases images are added and referenced from the
   READMEs; the card image uses placeholder speaker names. Optional: device page
   and Debug view.
4. **Enable repository features** (optional): Issues, Discussions, private
   vulnerability reporting, wiki.
5. **Set branch protection on `main`** (require pull request reviews, require
   status checks: ruff, pytest, hassfest).
6. **Flip visibility:** Settings > Danger zone > Change repository visibility >
   public. (Done by the repo owner, not by this automation.)
7. **Run the HACS validation workflow** after going public (expected to fail
   while private).
8. **Tag `v1.2.1`** to trigger the release workflow and build
   `tts_broadcast.zip`.
9. **Add the repo to HACS** as a custom repository and test the install on a
   clean Home Assistant.
10. **(Optional, later)** Submit to the HACS default list. Link to the current
    requirements and verify them before submitting.

## Do NOT do these yourself (user-only actions)

- Changing repository visibility (private -> public).
- Tagging a release / publishing to GitHub Releases.
- Submitting to the HACS default list.

## Why HACS validation fails while private

The HACS action validates against the GitHub repository; a private repository
cannot be reached by the HACS validation action without a token, so it reports a
failure. Tests and Hassfest are green. Once public, HACS validation should pass.
