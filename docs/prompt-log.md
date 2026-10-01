# Prompt Log

## 2026-10-01

- **Task 001 plan — User-Agent lacked contact info.** The plan's default `User-Agent` for the MET Norway probe had no contact information, which MET's terms of service require. Rejected the plan and had the agent use the repo URL instead: `weather-demo-live/0.1 github.com/zetsukko/weather-demo-live`.
- **Unrequested push during scaffolding.** While scaffolding the project, the agent pushed to GitHub without being asked.
- **GitHub token in git remote URL.** The agent found a GitHub token embedded in the `origin` remote URL. Revoked the token and switched to credential-manager login (`git remote set-url origin https://github.com/zetsukko/weather-demo-live.git`).
