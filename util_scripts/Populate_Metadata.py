# coding=utf-8
'''
-----------------------------------------------------------------------------
  Copyright (C) 2015 Glencoe Software, Inc. All rights reserved.


  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along
  with this program; if not, write to the Free Software Foundation, Inc.,
  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

------------------------------------------------------------------------------

Populate metadata from CSV.
'''

from omero.gateway import BlitzGateway
from omero.rtypes import rstring
import omero.scripts as scripts
from omero.model import PlateI, ScreenI

from omero.util.populate_roi import DownloadingOriginalFileProvider
from omero.util.populate_metadata import ParsingContext


def populate_metadata(client, conn, script_params):
    object_id = script_params["IDs"]
    file_annotation_ids = script_params["File_Annotations"]
    for file_annotation_id in file_annotation_ids:
        file_annotation = conn.getObject("FileAnnotation", file_annotation_id)
        print "Populating data from %s" % file_annotation.getFileName()
        original_file = file_annotation.getFile()._obj
        provider = DownloadingOriginalFileProvider(conn)
        file_handle = provider.get_original_file_data(original_file)
        if script_params["Data_Type"] == "Plate":
            omero_object = PlateI(long(object_id), False)
        else:
            omero_object = ScreenI(long(object_id), False)
        ctx = ParsingContext(client, omero_object, "")
        ctx.parse_from_handle(file_handle)
        ctx.write_to_omero()
    return "All done."


if __name__ == "__main__":
    dataTypes = [rstring('Plate'), rstring('Screen')]
    client = scripts.client(
        'Populate_Metadata.py',
        """
        """,
        scripts.String(
            "Data_Type", optional=False, grouping="1",
            description="Choose source of images",
            values=dataTypes, default="Plate"),

        scripts.Long(
            "IDs", optional=False, grouping="2",
            description="Object IDs."),

        scripts.List(
            "File_Annotations", optional=False, grouping="3",
            description="File annotation IDs containing metadata to populate."
        ).ofType(long),

        version="0.3",
        authors=["Emil Rozbicki"],
        institutions=["Glencoe Software Inc."],
        contact="emil@glencoesoftware.com",
    )

    try:
        # process the list of args above.
        scriptParams = {}
        for key in client.getInputKeys():
            if client.getInput(key):
                scriptParams[key] = client.getInput(key, unwrap=True)
        print scriptParams

        # wrap client to use the Blitz Gateway
        conn = BlitzGateway(client_obj=client)
        message = populate_metadata(client, conn, scriptParams)
        client.setOutput("Message", rstring(message))

    finally:
        client.closeSession()
