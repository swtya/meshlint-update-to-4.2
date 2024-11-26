![MeshLint Logo](/img/logo-suzanne.png "The default Monkey
has 32 Tris, 42 Nonmanifold Elements, and 9 6+-Edge Poles.")

A Blender Addon to help you keep your meshes clean and lint-free, like a
spell-checker for your meshes.

![Results with Suzanne](/img/messed-up-mesh.png "Found some
Issues.")

Can check for:

 - Tris: Evil.
 - Ngons: Also pretty bad.
 - Nonmanifold Elements: Stray Verts and Edges that have < or > than 2 faces.
 - Interior Faces: Faces spanning inside the mesh that cause confusing
     effects with Subsurf and Edge Loops. By the Blender definition, this is
     only true for a face if absolutely none of its edges are connected to <=
     2 faces.
 - 6+-Poles: Verts with 6 or more edges (check disabled by default, because
   some meshes legitimately have these).
 - Default Names (like `Cube.002`)
 - Unapplied Scale (remember that `Ctrl+a,s` This causes so many problems I
   don't even plan on making it an optional warning. If you have a selection
   that includes an object with an Unapplied Scale, you'll hear about it from
   MeshLint)
 - ...can you think of more? We'll add them!

So if you click `Select Lint`, in Object or Edit Modes, it will set your
current selection to all elements that fail the enabled checks. A good thing
to do if you are having trouble finding pieces is to hit `Numpad '.'`, which
will center the 3D Viewport on the problems. You might have to do this
iteratively with `b`order selects and `Middle Mouse Button` to deselect the
elements you already know about.

![Live Update Screenshot](/img/infobar.png "Live update
screenshot.")

Also, you can enable `Continuous Check`, which is a huge aspect to this. It is
good for cases where you think you won't be creating any new problem geometry.
Whenever something goes wrong, the Info Bar at the top will display a message
describing what MeshLint found. Also, you will notice the counts are updated.

Furthermore, it works on the whole selection (but starting with the Active
Object). So you can quickly check your entire scene with `a` to Select All and
then click `Select Lint`. The checker will stop on the first found bit of
lint, and throw you into Edit Mode so you can see it.

And finally, it now has a `Deselect all Lint-free Objects` button. This is a
process improvement for the "whole scene" checks, allowing you to see a better
overview.

Installing
----------
Download the release ZIP, extract this to the correct folder depending on your
operating system. See [Blender Extensions Dir](https://docs.blender.org/manual/en/latest/advanced/blender_directory_layout.html)

Advanced technique: 
The super-awesome way is to directly symlink `__init__.py` from your git into
the extension folder. The advantage is that the previous section's `git pull` 
will download the newest version automatically.

![Installing Addon](/img/install-addon.png "`Install
Addon...` screen.")

Hit `Ctrl+,` to open up the Edit -> Preferences... Then click 'Get Extensions'
tab. MeshLint should show in the installed group if the directory/files have
been found. Then jump to the "Add-ons" tab and tick the square next to MeshLint

![The Enable Checkbox](/img/enable-checkbox.png "The Enable
checkbox.")

If, for some reason, you have a hard time finding it, you can
search for `MeshLint`. 

The next time you run Blender you won't have to repeat the above.

![Where is it? -> In the Object Data
properties](/img/where-is-it.png "Object Data properties")

When installed, it will add a new Subpanel to the bottom of the `Object Data`
properties (the button in the `Properties Editor` that looks like the inverted
triangle). This is context sensitive and becomes visible when an appropriate 
object in the scene has first been selected.

The Name
--------

It comes from programming tools that do similar things, but for code
([Wikipedia Link](http://en.wikipedia.org/wiki/Lint\_(software\))). If you
program, you might want to Google about and see if such a thing exists for
your language. 

Going Further
-------------

We really want to make this a top-grade Addon. This will take a bit of
debugging and brainstorming, both. There's a spot right below this text for a
"Thanks", for users who give such feedback.

<rking@panoptic.com>

Getting Git
-----------

Best way is to:

    git clone git@github.com:ryanjosephking/meshlint.git

That way, you can `git pull` later on and it will automatically refresh to the
latest (theoretically-good) version.

But I realize that not everyone has `git` or an operating system capable of
symlinking.

So, for those that can't: You can simply download the
[__init__.py](https://raw.github.com/ryanjosephking/meshlint/master/__init__.py)
script directly. (And re-visit that URL for the newest version, later on.)


Thanks
-----

- [SavMartin](https://github.com/SavMartin/meshlint-Update-to-2.80/) / Sav
  Martin for making the port to 2.80
- [taniwha](http://taniwha.org/~bill/) / Bill Currie - For being part of the
  original idea and for Alpha and Beta testing.
- [endikos](http://www.endikos.com/) / William Knechtel - For also being an
  idea guy and tester, and for being a great Brother in the Lord, anyway.
- [lsmft](http://www.youtube.com/user/Ismft) / Kevin Wood - For being a
  premeir Beta tester, complete with a [UI improvement
  mockup](/img/lsmft.png "Likes Sending Me Fine
  Templates"), and also for providing the hardware that was used to write it.
  (!)
- [moth3r](http://www.moth3r.com/) / Ivan Šantić - For being one of the most
  enthusiastic Blenderers I ever met, and for testing/feedback, too.
- [encn](http://blenderartists.org/forum/member.php?102273-encn) - For the
  idea about "Deselect all Lint-free Objects", plus others.
