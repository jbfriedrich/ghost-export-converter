#!/usr/bin/env python

# Importing required modules (python-wordpress-xmlrpc >=2.3)
from wordpress_xmlrpc import Client, WordPressPost, WordPressTerm, WordPressPage
from wordpress_xmlrpc.methods import posts, taxonomies
import dateutil.parser
from time import sleep
import json
import argparse

# Parsing arguments
parser = argparse.ArgumentParser(
    prog='ghost2wp.py'
)
parser.add_argument(
    '-e',
    '--endpoint',
    type=str,
    help='XML-RPC API endpoint',
    required=True
)
parser.add_argument(
    '-f',
    '--file',
    type=str,
    help='Ghost JSON export file',
    required=True
)
parser.add_argument(
    '-p',
    '--password',
    type=str,
    help='Password for the Wordpress XML-RPC API',
    required=True
)
parser.add_argument(
    '-u',
    '--username',
    type=str,
    help='Username for the Wordpress XML-RPC API',
    required=True
)
args        = parser.parse_args()
filename    = args.file
wp_endpoint = args.endpoint
wp_user     = args.username
wp_pass     = args.password

# Preparing the XMLRPC client
client = Client(wp_endpoint, wp_user, wp_pass)

# Reading the ghost json export file
with open(filename) as f:
    text = f.read()

# Reading all posts, all tags and the post to tag mapping
data        = json.loads(text)
tags        = data['db'][0]['data']['tags']
all_posts   = data['db'][0]['data']['posts']
posts_tags  = data['db'][0]['data']['posts_tags']

# Go through all existing tags and create them
# in Wordpress with the same name, slug and id
for t in tags:
    slug            = t.get('slug', None)
    name            = t.get('name', None)

    tag             = WordPressTerm()
    tag.taxonomy    = 'post_tag'
    tag.name        = name
    tag.slug        = slug
    tag.id          = client.call(taxonomies.NewTerm(tag))

# Go through all existing posts
for p in all_posts:
    # If the post is really a 'post' and not a 'page'
    if p['page'] == 0:
        # If we do not have a published_at date, we use the created_at value
        date = p['published_at']
        if date is None:
            date = p['created_at']

        # Take the post_id from the post export, go through the post/tag map and
        # find all tag ids associated with the post. For every tag id we find
        # associated with the post, we loop through the tags and find the name
        # of the tag and add it to the t_tags list for later use
        t_tags  = []
        for e in posts_tags:
            if e['post_id'] == p['id']:
                for t in tags:
                    if t['id'] == e['tag_id']:
                        t_tags.append(t['name'])

        # Creating the Wordpress post object
        post = WordPressPost()
        # Trying to parse the post date to be displayed correctly in Wordpress
        # If the parsing fails we do nothing but continue with the import
        try:
            post.date = dateutil.parser.parse(date)
        except:
            continue

        post.terms_names = {
            'post_tag': t_tags
        }
        post.slug = p['slug']
        post.content = p['html']
        post.title = p['title']
        post.post_status = 'publish'
        # Finally publishing the post
        post.id = client.call(posts.NewPost(post))
    else:
        page = WordPressPage()
        page.title = p['title']
        page.content = p['html']
        page.post_status = 'publish'
        page.id = client.call(posts.NewPost(page))
