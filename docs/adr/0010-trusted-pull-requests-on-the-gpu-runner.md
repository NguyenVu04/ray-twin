# 10. Trusted pull requests on the GPU runner

- **Status:** Accepted
- **Date:** 2026-10-29
- **Deciders:** Nguyễn Duy Vũ
- **Supersedes:** —
- **Superseded by:** —

## Context

The TR runs a self-hosted GPU runner on every pull request (component 5 in [TR §14.3](../technical-report.html#mvp-tieu-chi), [TR Appendix A](../technical-report.html#quyet-dinh)). GPU acceptance needs these tests ([TR §14.4](../technical-report.html#mvp-nghiem-thu)).

The repository is public. The GPU runner is the development laptop, which boots Linux or Windows. A pull-request workflow runs the code of the pull request. If the workflow runs on the laptop, a pull request from a fork can run any code there. That code can read the SSH keys, tokens and browser sessions of the owner. GitHub recommends that public repositories do not use self-hosted runners for this reason.

## Decision

1. The GPU workflow runs on runners with the labels `self-hosted` and `gpu`.
2. The GPU job runs automatically for a pull request when both conditions are true:
   - The head branch is in this repository.
   - The author is the owner, a member or a collaborator.
3. For a pull request from a fork, the GPU job runs only on a `labeled` event with the label `gpu-ok`. The owner adds the label after reading the diff. A new commit does not start the GPU job. The owner removes the label and adds it again after reading the new commit.
4. The repository requires approval for workflow runs from all outside collaborators.
5. The GPU workflow never uses `pull_request_target`. It has no secrets, and its `GITHUB_TOKEN` has only `contents: read`.
6. The runner service runs under a dedicated operating-system user. That user has no access to the home directory, SSH keys or browser profiles of the owner. Each of the two operating systems on the laptop registers its own runner, with the labels `gpu` and the OS name.
7. CPU jobs run on GitHub-hosted runners for every pull request.

## Consequences

**Positive**

- Code from a fork never runs on the laptop without a review.
- Pull requests from trusted authors still get GPU tests automatically.
- Every pull request gets the CPU tests and the oracle comparison.

**Negative**

- A pull request from a fork needs a manual step for each new commit.
- The label depends on the judgment of the owner. A harmful diff can still pass a review.
- GPU tests run only while the laptop is on and booted into the requested operating system.
- A pull request can merge before its GPU test runs. Branch protection must make that state visible ([TR §15](../technical-report.html#rui-ro)).
- The dedicated runner user needs configuration on both operating systems.

**Neutral**

- GitHub-hosted GPU runners can replace the laptop later, at a cost per minute.

## Alternatives considered

**GPU tests on every pull request, also from forks (TR).** All changes get GPU tests before merge. Rejected because code from any fork could run on the development laptop.

**GPU tests only on `main`, on a nightly schedule and on manual start.** No pull-request code runs on the laptop. Rejected because GPU failures would appear only after the merge.
