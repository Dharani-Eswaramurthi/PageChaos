# Releasing PageChaos

Maintainer: Dharani Eswaramurthi. Releases are explicit alpha previews.

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
3. Keep pyproject.toml and pagechaos.__version__ consistent.
4. Tag the reviewed commit v<version>; do not move a published release tag.
5. Run Release at that tag, selecting publish_to_pypi when the public upload
   is intended. The workflow tests and builds, uploads to TestPyPI, downloads
   and verifies the uploaded wheel, then waits for the pypi environment review.
6. Review the artifact checks and authorize the production environment job.
7. Verify installation from PyPI in a fresh environment and inspect project links.
8. Publish a GitHub pre-release at the same tag with the wheel, source archive,
   checksums, scope, known limitations, and feedback route.

The two indexes receive the same built artifacts from a single release run.
The production job has only artifact download and publishing steps.
Only publishing jobs receive id-token: write.

The TestPyPI upload allows existing filenames for reruns. The subsequent artifact
hash check must still match this run's build, so a changed artifact with an
already-used version cannot proceed to production. Use a new alpha version
when changing release contents after an upload.

## Corrections

Publish a new version rather than replacing previously uploaded files. Yank a
materially broken release with a useful reason when appropriate. Do not remove
working releases just to tidy the project page.

## References

- [PyPA release workflow guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
