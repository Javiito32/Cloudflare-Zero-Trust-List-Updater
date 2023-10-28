# Cloudflare Zero Trust List Manager

**🌩️** Keep your Cloudflare Zero Trust domain lists up to date automatically

## Description

Cloudflare Zero Trust List Manager is a project that dynamically updates the Cloudflare Trust domain lists. The project can obtain domain lists from a variety of sources, including domain list URLs and hostfiles.

The use for which this program was created was to keep the lists updated with domain and host lists used in solutions like [AdGuard](https://github.com/AdguardTeam/AdGuardHome) and [Pihole](https://github.com/pi-hole/pi-hole) to block ads and telemetry on any device connected with Cloudflare Zero Trust, but it can also be used for any other purpose that needs to update cloudflare lists from host files or domain lists hosted on the internet.

## Usage

To use the updater, you must fork this repository and set the following Actions Secrets with your Cloudflare credentials. The GitHub Action will automatically generate and update your lists with the GitHub Action:

* `API_TOKEN`: Your Cloudflare API key
* `IDENTIFIER`: Your Cloudflare account ID
* `SLACK_URL`: A Slack Webhook URL to get notifications

### Configuration

On the [lists.json](config/lists.json) file you can add/modify the lists that will be updated on your zero trust environment, the default config uses ~250 lists out of 300, the maximum amount of lists

## To do

- [x] Basic functionality
- [ ] Set the use of Slack Url optional
- [ ] Update lists and avoid creating/deleting lists if not necessary
- [ ] Investigate the viability to add regexp filters

## Collaboration

To collaborate with the project, follow these steps:

1. Create a GitHub account.
2. Create a pull request for your contribution.
3. A reviewer will review your contribution and notify you if it is accepted or not.

## License

This project is under AGPL-3.0-only - Checkout [LICENSE](LICENSE) for more detail

<img src="https://em-content.zobj.net/source/microsoft-teams/363/keyboard_2328-fe0f.png" height="22" /> with <img src="https://em-content.zobj.net/source/microsoft-teams/363/red-heart_2764-fe0f.png" height="22" /> by [Javiito32](https://github.com/Javiito32) <img src="https://em-content.zobj.net/source/microsoft-teams/363/smiling-face-with-smiling-eyes_1f60a.png" height="22" />
