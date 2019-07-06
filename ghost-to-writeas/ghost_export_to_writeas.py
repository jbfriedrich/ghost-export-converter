#!/usr/bin/env python3
"""Ghost 2.x export DB to Write.as Converter.

Convert HTML posts from a Ghost 2.x export file into Markdown formatted files
and use the API to upload them to a Write.as Publication.
"""

from string import Template
from time import sleep
import argparse
import getpass
import html2text
import json
import os
import requests
import sys

# Some static generic variables
local_post_dir = 'posts'


def get_tagname(tags, tagid):
    """Get tag name from tag ID from extracted Ghost tags."""
    for tag in tags:
        if tag['id'] == tagid:
            return tag['name']


def get_post_tags(postid, posttags, tags):
    """Get post tags for post with certain postid from Ghost blog export."""
    _tags = []
    _nametags = []
    for item in posttags:
        if item['post_id'] == postid:
            _tags.append(item['tag_id'])
    for tag in _tags:
        nametag = get_tagname(tags, tag)
        _nametags.append(nametag)
    return _nametags


def read_ghost_export(ghost_export_fname):
    """Read Ghost blog export file and return posts, tags and posttags."""
    with open(ghost_export_fname, 'r') as f:
        ghostdb = json.load(f)
    _posts = ghostdb['db'][0]['data']['posts']
    _tags = ghostdb['db'][0]['data']['tags']
    _posttags = ghostdb['db'][0]['data']['posts_tags']
    return _posts, _tags, _posttags


def writeas_authenticate(username, password):
    """Authenticate with write.as API and get an authentication token."""
    writeas_auth_url = 'https://write.as/api/auth/login'
    writeas_content_header = {'Content-Type': 'application/json'}
    payload = {'alias': username, 'pass': password}
    r = requests.post(
        writeas_auth_url,
        headers=writeas_content_header,
        json=payload)

    if r.status_code == 200:
        result = r.json()
        token = result['data']['access_token']
        print(token)
        print("Successfully authenticated. Token: {}".format(token))
        return token
    else:
        print("Auth not successful. Response: {}".format(r.text))
        writeas_logout(writeas_auth_token)
        sys.exit(1)


def post_to_writeas(token, publication, post_title, post_date, post_content):
    """Post new blog post to write.as publication via API."""
    writeas_post_url = 'https://write.as/api/collections/{}/posts'.format(
        publication)
    writeas_auth_header = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    payload = {
        'title': post_title,
        'created': post_date,
        'body': post_content
    }
    r = requests.post(
        writeas_post_url,
        headers=writeas_auth_header,
        json=payload)

    if r.status_code == 201:
        result = r.json()
        post_id = result['data']['id']
        print('Post {} successfully created!'.format(post_id))
    else:
        print("Publishing post FAILED. Response: {}".format(r.text))
        writeas_logout(writeas_auth_token)
        sys.exit(1)


def writeas_logout(token):
    """Log the the user out and delete the auth token."""
    writeas_logout_url = 'https://write.as/api/auth/me'
    writeas_logout_header = {
        'Authorization': token,
        'Content-Type': 'application/json'
    }
    r = requests.delete(
        writeas_logout_url,
        headers=writeas_logout_header)

    if r.status_code == 204:
        print('User with token {} successfully logged out!'.format(token))
    else:
        print('Logout FAILED. Response: {}'.format(r.text))
        sys.exit(1)


if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(
        prog='convert_posts_to_markdown.py'
    )
    parser.add_argument(
        '-b',
        '--blog',
        type=str,
        help='Name of your Write.as publication (blog name)',
        required=True
    )
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='Filename of Ghost 2.x export',
        required=True
    )
    parser.add_argument(
        '-u',
        '--user',
        type=str,
        help='Write.as username',
        required=True
    )
    parser.add_argument(
        '-p',
        '--password',
        type=str,
        help='Write.as password'
    )
    args = parser.parse_args()
    ghost_export = args.file
    writeas_user = args.user
    writeas_pass = args.password
    writeas_publication = args.blog
    # Asking user for password if not specified on the commandline
    if writeas_pass is None:
        print("Please type in the password of your write.as account"
              " (there will be no output on the screen)")
        writeas_pass = getpass.getpass()

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.body_width = 0

    print("Creating directory for Markdown files...")
    if not os.path.exists(local_post_dir):
        try:
            os.mkdir(local_post_dir)
            print("Directory", local_post_dir, "successfully created")
        except IOError:
            print("Could not create directory", local_post_dir)
    else:
        print("Directory", local_post_dir, "already exists")

    print("Authenticating with the write.as API...")
    writeas_auth_token = writeas_authenticate(writeas_user, writeas_pass)

    print("Reading Ghost export database file...")
    posts, tags, posttags = read_ghost_export(ghost_export)

    print("Extracting posts from Ghost export...")
    for post in posts:
        post_info = {}
        post_info['id'] = post['id']
        post_info['title'] = '# {}'.format(post['title'])
        post_info['slug'] = post['slug']
        post_info['date'] = post['created_at']
        post_info['html_content'] = post['html']
        post_info['feature_image'] = post['feature_image']

        print("Extracting post '{}'...".format(post['title']))

        # Comment so I dont forget this nifty stuff here!
        # Get all post tag names and put them in a list
        post_tags = get_post_tags(post_info['id'], posttags, tags)
        # Prepend every item of that list with a # sign
        post_tags = ['#{}'.format(t) for t in post_tags]
        # Create one single string of all tags, joined with a comma
        post_tags = ' '.join(post_tags)
        # Last but not least, put that string into the dictionary
        post_info['tags'] = post_tags

        # Converting HTML content into Markdown content
        markdown = h.handle(post_info['html_content'])
        # Removing leading and trailing newline
        post_info['mdown_content'] = markdown.strip()

        filename = '{}/{}_{}.md'.format(
            local_post_dir,
            post_info['date'],
            post_info['slug']
        )

        if post_info['feature_image'] is not None:
            post_info['feature_image_mdown'] = '![Feature image]({})'.format(
                post_info['feature_image']
            )
            file_template = Template(
                '$title\n\n$feature_image_mdown\n\n$mdown_content\n\n$tags'
            )
            post_template = Template(
                '$feature_image_mdown\n\n$mdown_content\n\n$tags'
                )
        else:
            file_template = Template('$title\n\n$mdown_content\n\n$tags')
            post_template = Template('$mdown_content\n\n$tags')

        # Substituting values from post_info dictionary in the template
        file_content = file_template.substitute(post_info)
        # Doing the same for the content we will push to write.as
        post_content = post_template.substitute(post_info)

        print("Writing post to file", filename)
        with open(filename, 'w') as mdown_file:
            mdown_file.write(file_content)

        print("Publishing post on write.as blog '{}'...".format(
            writeas_publication)
        )
        post_to_writeas(
            writeas_auth_token,
            writeas_publication,
            post['title'],
            post_info['date'],
            post_content
        )
        # Sleep for 10 seconds before we go to the next post
        sleep(10)
    # After all the work is done, log out and invalidate the write.as token
    writeas_logout(writeas_auth_token)
