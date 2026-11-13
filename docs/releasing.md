# Releasing PageChaos

Maintainer: Dharani Eswaramurthi. Stable releases cover the documented API contract;
previews use an explicit alpha, beta, or release-candidate version suffix.

## Account configuration

Register the exact repository, workflow filename release.yml, and environment
name as a Trusted Publisher separately on PyPI and TestPyPI. Use the project
name pagechaos and repository owner Dharani-Eswaramurthi.

Create the testpypi and pypi GitHub environments. Protect pypi with a required
maintainer review and restrict deployment to version tags. A sole maintainer
must be allowed to review their own deployment. No stored PyPI token is needed.

## Release procedure

1. Review source changes, license material, documentation, and the changelog.
2. Run Validate successfully, including supported Python/platform jobs.
3. Keep pyproject.toml, pagechaos.__version__, and CITATION.cff consistent. For a
   stable release, use a final version such as 0.1.0, the Production/Stable
   classifier, and matching installation examples, security policy, and changelog.
   Run python scripts/check_install.py against a clean dist/ directory after the
   build and strict Twine checks. This checks a fresh core installation, extras,
   installed pytest discovery, the audit regression suite, and both CLI outcomes.
4. Tag the reviewed commit v<version>; do not move a published release tag.
5. Run Release at that tag, selecting publish_to_pypi when the public upload
   is intended. The workflow tests and builds, uploads to TestPyPI, downloads
   and verifies the uploaded wheel, then waits for the pypi environment review.
6. Review the artifact checks and authorize the production environment job.
7. Verify installation from PyPI in a fresh environment and inspect project links.
8. Download release-distributions from this successful Release run. Generate
   SHA256SUMS for its wheel and source archive; do not rebuild the release assets.
   Publish a GitHub release at the same tag with those three files, scope, known
   limitations, and feedback route. Mark a final version as the latest stable
   release; only versions with preview suffixes should be marked pre-release.

The two indexes receive the same built artifacts from a single release run.
The production job has only artifact download and publishing steps.
Only publishing jobs receive id-token: write.

The TestPyPI upload allows existing filenames for reruns. The subsequent artifact
hash check must still match this run's build, so a changed artifact with an
already-used version cannot proceed to production. Use a new version
when changing release contents after an upload.

## Corrections

Publish a new version rather than replacing previously uploaded files. Yank a
materially broken release with a useful reason when appropriate. Do not remove
working releases just to tidy the project page.

## References

- [PyPA release workflow guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
