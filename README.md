<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/header-dark.svg">
  <img src="./assets/header-light.svg" width="793" alt="Matthew Junkins. A miniature MITRE ATT&CK matrix with two techniques highlighted: T1059.001, suspicious PowerShell, and T1110, SSH brute force.">
</picture>

I build tools for security monitoring, detection engineering, and AI evaluation.

I'm a PC technician at Dominion Energy and a 2026 Cyber Security and Networking graduate from Shepherd University. At work I troubleshoot Windows and network issues, and I write guides that help coworkers use internal AI tools.

On my own time I build ways to spot suspicious activity and make it easier to investigate. I also evaluate AI-generated code and reasoning by checking what a model claims against the test output and the actual code changes.

I'm looking for entry-level roles in security operations, detection engineering, and AI evaluation. Reach me on [LinkedIn](https://www.linkedin.com/in/matthew-junkins-21809b268) or by [email](mailto:mjunkins445@gmail.com).

## Projects

### [Workflow Injection Guard](https://github.com/MatthewJunkins445/workflow-injection-guard)
Flags risky GitHub Actions patterns on the lines a pull request changes, using custom Semgrep rules backed by test fixtures and end-to-end checks.<br>
<sub>Built with GitHub Actions, Semgrep, and Python</sub>

### [L.O.G.S.](https://github.com/MatthewJunkins445/L.O.G.S.)
A desktop dashboard that puts network exposure, firewall findings, and live traffic alerts in one place.<br>
<sub>Built with React, Tauri, FastAPI, and Python</sub>

### Network Security Policy Simulator
A team capstone prototype for testing firewall policies and visualizing their effects.<br>
<sub>Network simulation and policy testing</sub>

## Detections

These are the highlighted squares in the matrix above.

| Detection | Data source | ATT&CK |
|---|---|---|
| Suspicious PowerShell execution | Sysmon → Splunk | [T1059.001](https://attack.mitre.org/techniques/T1059/001/) |
| SSH brute-force attempts | SSH auth logs → Splunk | [T1110](https://attack.mitre.org/techniques/T1110/) |
| Network anomaly alerts | Live traffic → [L.O.G.S.](https://github.com/MatthewJunkins445/L.O.G.S.) | Not mapped |

## Tools

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/tools-dark.svg">
  <img src="./assets/tools-light.svg" width="793" alt="Tools I use. Security: Splunk, Sysmon, Semgrep, Wazuh, Snort, Wireshark, MITRE ATT&CK. Languages: Python, PowerShell, JavaScript, Java, Bash. Frameworks: React, FastAPI, Tauri. Cloud and DevOps: AWS, Azure, Docker, GitHub Actions. Systems: Windows, Linux, Git, VS Code. Highlighted tools are used in a project or detection on this page.">
</picture>
