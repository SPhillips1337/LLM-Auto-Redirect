=== LLM Auto Redirect ===
Contributors: Gemini
Requires at least: 5.0
Tested up to: 6.5
Stable tag: 1.3.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Uses an LLM to suggest intelligent redirects for 404 errors found by the Redirection plugin.

== Description ==

This plugin is a powerful assistant for website managers who deal with a large number of 404 "Not Found" errors. It integrates with the popular "Redirection" plugin by John Godley to fetch a list of recent 404 errors.

Instead of manually deciding where to redirect each broken link, this plugin adds a "Suggest" button that sends the broken URL to a Large Language Model (like Google's Gemini). The AI analyzes the URL and, based on a list of your site's main pages, suggests the most logical and contextually relevant page to redirect to.

For example, a 404 for /events/community-fair-2022/ would likely result in a suggestion to redirect to your main /events/ page. A completely random or irrelevant 404 would default to the homepage.

Once you're happy with the suggestion, a "Create" button automatically adds the 301 redirect to the "Redirection" plugin and clears the original 404 log entry.

== Installation ==

IMPORTANT: You must have the "Redirection" plugin by John Godley installed and activated.

=== Installer Script ===

A hardened installer is available for trusted environments. Review the script before running it, especially when using the download form below.

Raw installer URL:

https://raw.githubusercontent.com/SPhillips1337/LLM-Auto-Redirect/main/install.sh

Download, inspect, then run:

```bash
curl -fsSLO https://raw.githubusercontent.com/SPhillips1337/LLM-Auto-Redirect/main/install.sh
less install.sh
bash install.sh --target /var/www/html/wp-content/plugins/llm-auto-redirect
```

Trusted one-line install:

```bash
curl -fsSL https://raw.githubusercontent.com/SPhillips1337/LLM-Auto-Redirect/main/install.sh | bash -s -- --target /var/www/html/wp-content/plugins/llm-auto-redirect
```

If you are already inside a clone of this repository, run:

```bash
./install.sh
```

The installer validates that existing non-empty targets are this plugin before updating them. Use `--force` only after verifying the target directory is safe to update.

=== Manual Install ===

Create a folder named `llm-auto-redirect` in your `/wp-content/plugins/` directory.

Place the plugin files from this repository into that folder, including `LLM_Auto_Redirect.php`.

Activate the "LLM Auto Redirect" plugin through the 'Plugins' menu in WordPress.

Go to Tools -> LLM Auto Redirect.

Configure your preferred LLM provider and save changes.

You can now start using the suggestion feature!
