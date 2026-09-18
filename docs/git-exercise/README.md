# Git exercise (disposable)

Practice the branch → pull request workflow on a file that doesn't matter. This directory is deleted after kickoff; nothing here is project evidence.

You already cloned the main repository at the start of the session. You've been added as a collaborator on `marek-sm/CANARY`, so you push branches straight to it. No fork needed.

## Steps

1. **Accept the invitation.** Open the collaborator invite from your GitHub notifications or email (or go to `https://github.com/marek-sm/CANARY/invitations`) and accept it. Until you do, `git push` is rejected.
2. **Tell Git who you are** (skip if already set). The repository is public, so use your GitHub no-reply address rather than a personal email (GitHub → Settings → Emails):

   ```
   git config --global user.name "Your Name"
   git config --global user.email "ID+handle@users.noreply.github.com"
   ```

3. **Branch, add one file, commit:**

   ```
   git switch main
   git pull
   git switch -c git-exercise/YOUR-HANDLE
   ```

   Create `docs/git-exercise/YOUR-HANDLE.md` with a single line, `Hello from YOUR-HANDLE`, and nothing else personal. Then:

   ```
   git add docs/git-exercise/YOUR-HANDLE.md
   git commit -m "chore: git exercise for YOUR-HANDLE"
   git push -u origin git-exercise/YOUR-HANDLE
   ```

4. **Open the pull request.** GitHub shows a **Compare & pull request** banner on `marek-sm/CANARY`. The base is `main`. Fill in the template's Scope section and add your reviewer in the **Reviewers** field.
5. **Review.** Your reviewer leaves a comment or an approval on your pull request.

Each person adds their own file on their own branch, so pull requests don't conflict. Never push directly to `main`.

## If `git push` asks for a password

GitHub no longer accepts account passwords over HTTPS. Don't debug credentials in the session. Do step 3 in the browser instead: on `marek-sm/CANARY`, use **Add file → Create new file**, name it `docs/git-exercise/YOUR-HANDLE.md`, choose **Create a new branch for this commit and start a pull request**, name the branch `git-exercise/YOUR-HANDLE`, then continue with step 4. Set up SSH or `gh auth login` afterwards.
