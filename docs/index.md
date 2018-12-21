# Content Cards Admin

This repo contains data and image files that control the content for
various parts of some pages on instances of [Bedrock][] (e.g. [www.mozilla.org][]).
The data files are [Markdown][] with [YAML front matter][yfm] similar to those of 
popular static site/blog generators like [Hugo][] and [Jekyll][].  

## Directory Structure

The directory layout and file names have meaning:

    content/                     # folder for all of the data
        home/                    # one folder per bedrock page
            card_1.en-US.md      # card named "card_1" in "en-US" locale
            card_1.de.md         # same card but in "de" locale
            the_dude.en-US.md    # card named "the_dude"
            
    static/                      # folder for all static assets
        img/                     # img folder in case we ever need other kinds
            home/                # folder per page (not required)
                dude-abides.jpg  # image referenced from "image: home/dude-abides.jpg" in card

Images should also go into the `img` folder, but the structure under that can be whatever
makes the most sense to you. Having at least a folder per page name that matches that of the data
seems like a good first layer. The `home` directory under `content` above is important however,
because it is the name by which you'll refer to all of the cards for that page when you fetch
them in a bedrock view.

## Data File Structure

The data in each file can really be any YAML you want. For the `home` cards the data names are
basically the argument names for [the `card()` macro in bedrock][card macro]. This allows for more
flexibility in that you can specify any argument for that macro in your data if you need to. Some
data is specially handeled however:

* `image` is processed in this repo and converted to `image_url` in bedrock since bedrock
  knows the real static URL. Same for `include_highres_image`. These values should be relative
  to the `static/img/` folder in this repo and the file(s) will be checked to make sure it exists.
* If you don't provide a `ga_title` it will be set to `title`. You may need to provide `ga_title`
  in situations where the `title` is in a different language than you'd like the GA data.
* `media_icon` should just be the short name, e.g. "video" or "audio" and will be converted to the
  full protocol class value by bedrock.
* `size` should also be the short name "small", "medium", "large", "extra-small". If omitted
  "small" is the default.
* Similar to the above 2 `aspect_ratio` should be set to simply "1-1" or "16-9" etc.
* `link_url` can be either a full URL (starting with `https://`) or a URL name in bedrock
  that will be converted to a URL using Django's `reverse()` function. Be careful using this
  as changes to a URL name in bedrock or a miss-spelling here can cause pages to error.

Here is an example file.

```yaml
---
# content/home/card_1.en-US.md
title: "We keep your data safe, never sold."
image: "home/ffyr.png"
link_url: "firefox.fights-for-you"
tag_label: "Video"
size: "large"
aspect_ratio: "16-9"
include_highres_image: true
desc: "You have the right to your own life — and your own data. Everything we make and do fights for you."
youtube_id: "rZAQ6vgt8nE"
media_icon: "video"
---

If there was markdown content it would go *here*.
```

We aren't currently using the Markdown content for the home page data, but it does work and is synced
to the bedrock database for future use. Also note that any unicode character should work ([emoji included][]).

## Deployment Process

Once a change to these files is merged to the `master` branch a process in our CI does several things:

1. Calculates the md5 hash of the image file contents and adds that hash to the file name. This is similar
   to what Bedrock does to other static media and is what is called an "immutable file" for caching, since any
   change to the file will result in a different file name. This allows us to set the maximum cache expire times.
2. Check to make sure that every image file (including high-res) referenced in a data file exists in the `static/img`
   directory and has been processed.
3. Process the YAML and Markdown in the data files and output `.json` files that are easier to load by bedrock.
4. Upload the static files to the s3 bucket for whichever site instance will be needed. `master` branch
   changes go to dev, and `prod` branch changes go to stage and prod.
5. Commit the changed images and new `.json` files to a new `master-processed` branch and push that to the repo.

Bedrock itself will load the files from these `{master,prod}-processed` branches (depending on which bedrock it is).
You should see notifications of the CI process in the `#www-notify` channel on Slack.

[Bedrock]: https://github.com/mozilla/bedrock
[www.mozilla.org]: https://www.mozilla.org/
[Markdown]: https://daringfireball.net/projects/markdown/
[yfm]: https://jekyllrb.com/docs/front-matter/
[Jekyll]: https://jekyllrb.com/
[Hugo]: https://gohugo.io/
[card macro]: https://github.com/mozilla/bedrock/blob/7905b03598a73b1f9bd5e3c3b3589180d6f103c3/bedrock/base/templates/macros-protocol.html#L98
[emoji included]: https://github.com/mozmeao/www-admin/blob/32f20b08cd1c286d952e1c65c09c2ebb950e7678/content/home/card_4.en-US.md

*[CI]: Continuous Integration
