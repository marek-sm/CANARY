# Git exercise (disposable)

Practice the fork → branch → pull request workflow on a file that doesn't matter. This directory is deleted after kickoff; nothing here is project evidence.

You already cloned the main repository at the start of the session. You don't need push access to it: you push to your own fork and open a pull request from there.

## Steps

1. **Fork.** On GitHub, open `marek-sm/CANARY` and click **Fork**.
2. **Tell Git who you are** (skip if already set). The repository is public, so use your GitHub no-reply address rather than a personal email (GitHub → Settings → Emails):

   ```
   git config --global user.name "Your Name"
   git config --global user.email "ID+handle@users.noreply.github.com"
   ```

3. **Add your fork as a remote** from inside your existing `CANARY` clone:

   ```
   git remote add fork https://github.com/YOUR-HANDLE/CANARY.git
   ```

4. **Branch, add one file, commit:**

   ```
   git switch -c git-exercise/YOUR-HANDLE
   ```

   Create `docs/git-exercise/YOUR-HANDLE.md` with a single line, `Hello from YOUR-HANDLE`, and nothing else personal. Then:

   ```
   git add docs/git-exercise/YOUR-HANDLE.md
   git commit -m "chore: git exercise for YOUR-HANDLE"
   git push -u fork git-exercise/YOUR-HANDLE
   ```

5. **Open the pull request.** GitHub shows a **Compare & pull request** banner on your fork. The base is `marek-sm/CANARY` `main`. Fill in the template's Scope section and @-mention your reviewer in the description. Without write access you can't set the Reviewers field, and that's expected.
6. **Review.** Your reviewer leaves a comment or an approval on your pull request.

Each person adds their own file, so pull requests don't conflict.

## If `git push` asks for a password

GitHub no longer accepts account passwords over HTTPS. Don't debug credentials in the session. Do step 4 in the browser instead: on **your fork**, use **Add file → Create new file**, name it `docs/git-exercise/YOUR-HANDLE.md`, commit it to a new branch, then continue with step 5. Set up SSH or `gh auth login` afterwards.
