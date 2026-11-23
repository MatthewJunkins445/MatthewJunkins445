<h1 align="center">Matthew Junkins</h1>

<p align="center"><strong>I build tools for security monitoring, detection engineering, and AI evaluation.</strong></p>

<p align="center">
  <a href="#detection-engineering"><img src="https://img.shields.io/badge/Detection%20Engineering-0E7490?style=for-the-badge" alt="Jump to Detection Engineering" /></a>
  <a href="#featured-projects"><img src="https://img.shields.io/badge/Application%20Security-4338CA?style=for-the-badge" alt="Jump to Application Security" /></a>
  <a href="#about"><img src="https://img.shields.io/badge/AI%20Evaluation-6D28D9?style=for-the-badge" alt="Jump to AI Evaluation" /></a>
</p>

<p align="center">
  <a href="#toolbox">Toolbox</a> · <a href="#featured-projects">Featured Projects</a> · <a href="#connect">Connect</a>
</p>

## About

I’m a PC technician at Dominion Energy and a Cyber Security and Networking graduate from Shepherd University. I troubleshoot Windows and network issues, and write guides that help coworkers use internal AI tools.

My projects look at how to spot suspicious activity and make the results easier to investigate. I also evaluate AI-generated code and reasoning by comparing the model’s claims with the test output and the code changes.

## Toolbox
**Languages**
<p>
  <img src="https://skillicons.dev/icons?i=py,powershell,js,java,bash" alt="Python, PowerShell, JavaScript, Java, Bash" />
</p>

**Frameworks & Libraries**
<p>
  <img src="https://skillicons.dev/icons?i=react,fastapi,tauri" alt="React, FastAPI, Tauri" />
</p>

**Cloud & DevOps**
<p>
  <img src="https://skillicons.dev/icons?i=aws,azure,docker,githubactions" alt="AWS, Azure, Docker, GitHub Actions" />
</p>

**Systems**
<p>
  <img src="https://skillicons.dev/icons?i=windows,linux,git,github,vscode" alt="Windows, Linux, Git, GitHub, VS Code" />
</p>

**Security**
<p>
  <img src="https://img.shields.io/badge/Splunk-000000?style=for-the-badge&logo=splunk&logoColor=white" alt="Splunk" />
  <img src="https://img.shields.io/badge/Sysmon-0078D4?style=for-the-badge" alt="Sysmon" />
  <img src="https://img.shields.io/badge/Wazuh-1E40AF?style=for-the-badge&logo=wazuh&logoColor=white" alt="Wazuh" />
  <img src="https://img.shields.io/badge/Snort-B91C1C?style=for-the-badge" alt="Snort" />
  <img src="https://img.shields.io/badge/Wireshark-1679A7?style=for-the-badge&logo=wireshark&logoColor=white" alt="Wireshark" />
  <img src="https://img.shields.io/badge/Semgrep-0E7490?style=for-the-badge&logo=semgrep&logoColor=white" alt="Semgrep" />
  <img src="https://img.shields.io/badge/MITRE%20ATT%26CK-7F1D1D?style=for-the-badge" alt="MITRE ATT&CK" />
</p>

## Featured Projects
| Project | What it is | Stack |
|---|---|---|
| [Workflow Injection Guard](https://github.com/MatthewJunkins445/workflow-injection-guard)<br><sub>Application security</sub> | Flags risky GitHub Actions patterns on the lines a pull request changes, using custom Semgrep rules with test fixtures and end-to-end checks. | GitHub Actions + Semgrep + Python |
| [L.O.G.S.](https://github.com/MatthewJunkins445/L.O.G.S.)<br><sub>Network monitoring</sub> | A desktop dashboard that shows network exposure, firewall findings, and live traffic alerts in one place. | React + Tauri + FastAPI + Python |
| Network Security Policy Simulator<br><sub>Team capstone</sub> | A prototype for testing firewall policies and visualizing their effects. | Network simulation + Policy testing |

## Detection Engineering
| Detection | Data source | ATT&CK |
|---|---|---|
| Suspicious PowerShell execution | Sysmon → Splunk | [T1059.001](https://attack.mitre.org/techniques/T1059/001/) |
| SSH brute-force attempts | SSH auth logs → Splunk | [T1110](https://attack.mitre.org/techniques/T1110/) |
| Network anomaly alerts | Live traffic → [L.O.G.S.](https://github.com/MatthewJunkins445/L.O.G.S.) | — |

## 3D Commit History
<!--
  Regenerated daily by .github/workflows/profile-3d.yml.
  Colors live in .github/profile-3d-settings.json (cyan -> violet, with a dark-mode palette).
-->
<p align="center">
  <img src="./profile-3d-contrib/profile-cyan-violet.svg" width="900" alt="Isometric 3D graph of my GitHub contribution history" />
</p>

## Connect
- [LinkedIn](https://www.linkedin.com/in/matthew-junkins-21809b268)
- [Email](mailto:mjunkins445@gmail.com)
- [GitHub](https://github.com/MatthewJunkins445?tab=repositories)
