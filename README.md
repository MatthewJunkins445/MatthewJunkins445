<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/header-dark.svg">
  <img src="./assets/header-light.svg" width="793" alt="Matthew Junkins. A miniature MITRE ATT&CK matrix with two techniques highlighted: T1059.001, suspicious PowerShell, and T1110, SSH brute force.">
</picture>

I build tools for security monitoring, detection engineering, and AI evaluation.

I'm a PC technician at Dominion Energy and a 2026 Cyber Security and Networking graduate from Shepherd University. At work I troubleshoot Windows and network issues, and I write guides that help coworkers use internal AI tools.

On my own time I build ways to spot suspicious activity and make it easier to investigate. I also evaluate AI-generated code and reasoning by checking what a model claims against the test output and the actual code changes.

I'm looking for entry-level roles in security operations, detection engineering, and AI evaluation. Reach me on [LinkedIn](https://www.linkedin.com/in/matthew-junkins-21809b268) or by [email](mailto:mjunkins445@gmail.com).

## Tools and pinned projects

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/tools-dark.svg">
  <img src="./assets/tools-light.svg" width="793" alt="Tools I use, grouped by area. Security: Splunk, Sysmon, Wazuh, Snort, Wireshark, MITRE ATT&CK, Semgrep. Languages: Python, PowerShell, JavaScript, Java, Bash. Frameworks: React, FastAPI, Tauri. Cloud and DevOps: AWS, Azure, Docker, Git, GitHub Actions. Systems: Windows, Linux, VS Code. Highlighted: Semgrep and GitHub Actions in Workflow Injection Guard; Python in all pinned projects; React, FastAPI, and Tauri in L.O.G.S.">
</picture>

<p>
<a href="https://github.com/MatthewJunkins445/workflow-injection-guard"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/pin-wig-dark.svg"><img src="./assets/pin-wig-light.svg" width="258" alt="Workflow Injection Guard: Flags risky GitHub Actions patterns on the lines a pull request changes. Built with Semgrep, GitHub Actions, Python."></picture></a>
<a href="https://github.com/MatthewJunkins445/L.O.G.S."><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/pin-logs-dark.svg"><img src="./assets/pin-logs-light.svg" width="258" alt="L.O.G.S.: A desktop dashboard for network exposure, firewall findings, and live traffic alerts. Built with React, Tauri, FastAPI, Python."></picture></a>
<a href="https://github.com/MatthewJunkins445/mcp-gateway"><picture><source media="(prefers-color-scheme: dark)" srcset="./assets/pin-mcp-dark.svg"><img src="./assets/pin-mcp-light.svg" width="258" alt="MCP Gateway: A local MCP proxy that only exposes approved tools whose definitions match a lock file. Built with Python."></picture></a>
</p>

I also worked on a team capstone, a Network Security Policy Simulator for testing firewall policies and visualizing their effects.

## Detections

These are the highlighted squares in the header.

| Detection | Data source | ATT&CK |
|---|---|---|
| Suspicious PowerShell execution | Sysmon → Splunk | [T1059.001](https://attack.mitre.org/techniques/T1059/001/) |
| SSH brute-force attempts | SSH auth logs → Splunk | [T1110](https://attack.mitre.org/techniques/T1110/) |
| Network anomaly alerts | Live traffic → [L.O.G.S.](https://github.com/MatthewJunkins445/L.O.G.S.) | Not mapped |
