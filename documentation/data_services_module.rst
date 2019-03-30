.. This is A COPY OF the main index.rst file which is rendered into the landing page of your documentation.
   Follow the inline instructions to configure this for YOUR next project.



Data Services Module
====================
|

The data services module id composed of two major parts - the preprocessor,
and the busy-index provider.

|

The Preprocessor
++++++++++++++++

Loads bus routes and perform aggregation
to discover likely congested geo-temporal slices.

In practice this means that we take a certain geo-temporal resolution
(for example, a 100m. radius and 10 min.), and if a specific bus spent at least
3 minutes in this geo-temporal slice, we say it is stuck.

Then we take only slices where at least 2 buses were stuck together,
and say these slices are busy.

Finally, the average time a bus spent in a busy slice is the "busy index" of that slice.

The data of the busy slices, together with their busy index, is saved to serve as a static DB.


|

.. image:: C:\\Users\\dalya\\Documents\\civilhack-2019\\documentation\\_static\\preprocessor.jpg

|

The Busy Index Provider
+++++++++++++++++++++++

Given a time in the day, and how long to see into the future (default 60 minutes),
aggregate the busy geo-temporal slices and output in a .json format that maps
busy lat-lng points and their corresponding busy-index.

|


.. maxdepth = 1 means the Table of Contents will only links to the separate pages of the documentation.
   Increasing this number will result in deeper links to subtitles etc.

.. Below is the main Table Of Content
   You have below a "dummy" file, that holds a template for a class.
   To add pages to your documentation:
        * Make a file_name.rst file that follows one of the templates in this project
        * Add its name here to this TOC


.. toctree::
   :maxdepth: 1
   :name: mastertoc

   preprocessor
   preprocessor_runner
   busy_index_provider
   busy_index_provider_runner


.. Delete this line until the * to generate index for your project: * :ref:`genindex`


|

This documentation was last updated on |today|.

.. Finished personalizing all the relevant details? Great! Now make this your main index.rst,
   And run `make clean html` from your documentation folder :)
