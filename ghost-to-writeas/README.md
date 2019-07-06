# Ghost to Write.as Importer

This script can be used to export your blog posts from your Ghost 2.x export file and post them on your Write.as publication. 

It extracts all posts into local Markdown files, residing in a newly created 'posts' subdirectory. All tags, feature image URLs and publishing dates are preserved. The script uses the write.as [public API](https://developers.write.as/docs/api/).

## Installation
- Make your you have a working [Python 3.x installation](https://realpython.com/installing-python/)
- Clone this repo to your local hard drive
- Install all required modules via `pip install -r requirements`
- Run the script and follow the instructions

## Usage
![usage image](https://rmbr.eu/file/cldcdn/19/3/ghost2writeas_readme_image.png)

## Requirements
- Ghost 2.x blog [export](https://docs.ghost.org/faq/the-importer/)
- Write.as account
- Python 3.x
- Python modules:
    - requests
    - html2text

## Notes

The new editor that was introduced with [Ghost 2.0](https://blog.ghost.org/2-0/) is creating new posts in [MobileDoc](https://github.com/bustle/mobiledoc-kit) (and not Markdown) by default. If you do not use the Markdown card in the new editor, there is no Markdown version of your post in the database. But there is always an HTML version of your post created. For that reason I decided to convert the HTML post into Markdown. This Markdown conversion is not always 100% accurate. Please review your posts after they are published on write.as.

Please be aware that Ghost 1.x exports are not supported by this script. It was never tested with such old Ghost versions – it might work, or it might not.
