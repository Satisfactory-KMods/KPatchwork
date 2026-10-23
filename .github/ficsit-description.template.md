<table width="100%" cellpadding="0" cellspacing="0" style="border:none;background:#1a1a2e;border-radius:12px;overflow:hidden;margin-bottom:16px">
<tr>
<td width="140" style="padding:20px 16px 20px 24px;vertical-align:middle;border:none">
  <a href="{{DISCORD_URL}}">
    <img src="https://raw.githubusercontent.com/Kyri123/KMods-Docs/main/docs/Images/KMods-Logo.png" height="100" width="100" alt="KMods Logo" />
  </a>
</td>
<td style="padding:20px 24px 20px 0;vertical-align:middle;text-align:right;border:none">
  <div>
    <a href="{{DISCORD_URL}}"><img src="https://img.shields.io/badge/Discord-Join%20Us-5865F2?style=for-the-badge&logo=discord&logoColor=white" height="28" alt="Discord" /></a>
    &nbsp;
    <a href="{{PATREON_URL}}"><img src="https://img.shields.io/badge/Patreon-Support%20Us-F96854?style=for-the-badge&logo=patreon&logoColor=white" height="28" alt="Patreon" /></a>
  </div>
  <div style="margin-top:8px">
    <a href="{{FICSIT_PROFILE_URL}}"><img src="https://img.shields.io/badge/ficsit.app-KMods-009688?style=for-the-badge" height="28" alt="ficsit.app" /></a>
    &nbsp;
    {{MULTIPLAYER_BADGE}}
  </div>
</td>
</tr>
</table>

<br />

<table width="100%" cellpadding="0" cellspacing="0" style="border:none">
<tr>
<td style="padding:4px 0;border:none">
  <a href="https://k-mods.com"><img src="https://img.shields.io/badge/k--mods.com-Website-e8a202?style=flat-square" alt="k-mods.com" /></a>
  &nbsp;
  <a href="https://github.com/Satisfactory-KMods/KPatchwork"><img src="https://img.shields.io/badge/GitHub-Contribute-181717?style=flat-square&logo=github" alt="Contribute on GitHub" /></a>
  &nbsp;
  <a href="https://docs.k-mods.com/kdataforge/"><img src="https://img.shields.io/badge/KDataForge-Documentation-1f8acb?style=flat-square" alt="KDataForge Documentation" /></a>
</td>
</tr>
</table>

---

**Patchwork: Cross-Mod Compatibility Packs** (`KPatchwork`) keeps independently developed Satisfactory mods working together. It ships small, conditional KDataForge packs that activate only when their exact mod combination is installed.

No settings, load-order guessing, or manual recipe edits: install KPatchwork and supported combinations receive their compatibility changes automatically.

---

<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:#e8a202;padding:6px 14px;border-radius:6px 6px 0 0;border:none"><strong style="color:#1a1a2e;font-size:18px">Current Compatibility Packs</strong></td></tr></table>

This release contains **{{PACK_COUNT}}**. Pack list, supported mods, versions, maintainers, and included patch groups come directly from current `pack.yml` files and pack contents.

{{PACK_CATALOG}}

---

<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:#e8a202;padding:6px 14px;border-radius:6px 6px 0 0;border:none"><strong style="color:#1a1a2e;font-size:18px">How It Works</strong></td></tr></table>

- Each compatibility case lives in its own versioned pack.
- Pack conditions detect required mods before any patch loads.
- KDataForge applies recipe, schematic, research, data-asset, and other reflected-property changes at session start.
- Packs whose required mods are missing stay inactive.
- Dedicated servers receive identical pack content.

Restart session after changing installed mods so KDataForge can evaluate packs again.

<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="background:#e8a202;padding:6px 14px;border-radius:6px 6px 0 0;border:none"><strong style="color:#1a1a2e;font-size:18px">Contribute a Compatibility Pack</strong></td></tr></table>

Patchwork: Cross-Mod Compatibility Packs is community-driven. Add or update a focused pack under `DataForge/`, document what it changes in `pack.yml`, then open a pull request. CI validates ownership, YAML structure, package output, and generated page content.

[Repository and contribution guide](https://github.com/Satisfactory-KMods/KPatchwork)

---

<table width="100%" cellpadding="0" cellspacing="0" style="border:none;background:#1a1a2e;border-radius:12px;overflow:hidden;margin-top:16px">
<tr>
<td colspan="2" style="background:#e8a202;padding:0;border:none;height:4px"></td>
</tr>
<tr>
<td style="padding:20px 24px;border:none;vertical-align:middle">
  <strong style="color:#e8a202;font-size:14px">Questions, bugs, or compatibility requests?</strong><br />
  <span style="color:#94a3b8;font-size:12px">Join Discord or contribute a pack on GitHub</span>
</td>
<td style="padding:20px 24px 20px 0;text-align:right;border:none;vertical-align:middle">
  <table cellpadding="0" cellspacing="0" style="display:inline-table;border:none">
  <tr>
    <td style="padding:3px 4px;border:none"><a href="{{DISCORD_URL}}"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" height="28" alt="Discord" /></a></td>
    <td style="padding:3px 4px;border:none"><a href="{{PATREON_URL}}"><img src="https://img.shields.io/badge/Patreon-F96854?style=for-the-badge&logo=patreon&logoColor=white" height="28" alt="Patreon" /></a></td>
  </tr>
  <tr>
    <td style="padding:3px 4px;border:none"><a href="{{FICSIT_PROFILE_URL}}"><img src="https://img.shields.io/badge/ficsit.app-009688?style=for-the-badge" height="28" alt="ficsit.app" /></a></td>
    <td style="padding:3px 4px;border:none"><a href="https://github.com/Satisfactory-KMods/KPatchwork"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github" height="28" alt="GitHub" /></a></td>
  </tr>
  </table>
</td>
</tr>
</table>
