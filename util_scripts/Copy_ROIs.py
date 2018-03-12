# -*- coding: utf-8 -*-
"""
-----------------------------------------------------------------------------
  Copyright (C) 2018 Glencoe Software, Inc. All rights reserved.
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
"""


import logging
import sys

LOGGER = logging.getLogger('gs_util.metadata.eSlide')
LOGGING_FORMAT = "%(asctime)s %(levelname)-7s [%(name)16s] %(message)s"

OMERO_IMPORTED = False
try:
    import omero
    from omero.gateway import BlitzGateway
    from omero.rtypes import rstring
    import omero.scripts as scripts
    OMERO_IMPORTED = True
except Exception:
    OMERO_IMPORTED = False
    LOGGER.warn("OMERO lib not on the path.")


# Query to retrieve the ROIs for particular image
# externalInfo is used by PathViewer to find ROIs created in PathViewer
# externalInfo if exists is copied to new ROI
# this prevents the "Where was this ROI created?" dialog to pop up
ROI_QUERY = \
    "SELECT roi FROM Image as image " \
    "LEFT OUTER JOIN image.rois as roi " \
    "LEFT OUTER JOIN FETCH roi.details.externalInfo " \
    "LEFT OUTER JOIN FETCH roi.shapes " \
    "WHERE image.id = :id"


def get_rois_copy(conn, source_image_id, target_image_id):
    '''
    This method creates copies of ROIs from the source image
    and links them to the target image
    '''
    # Retrieve ROIs for source_image using ROI_QUERY
    params = omero.sys.ParametersI()
    params.addId(source_image_id)
    results = conn.getQueryService().findAllByQuery(
        ROI_QUERY, params, _ctx={'omero.group': '-1'})
    # Check if the query result is None:
    if len(results) == 1 and results[0] is None:
        return []
    LOGGER.info("Found %i ROIs to copy" % len(results))
    # OMERO.image to link the ROIs to:
    target_image = omero.model.ImageI(target_image_id, False)
    # Copy ROIs in a loop:
    for roi in results:
        # Log ROI details:
        roi_name = roi.name if roi.name is None else roi.name.val
        LOGGER.info("Copying ROI name: %s, id: %i" % (roi_name, roi.id.val))
        # Set copy ID to None - this way server knows we want to create a new
        # ROI and not update existing one:
        roi.id = None
        # Get the externalInfo:
        externalInfo = roi.details.externalInfo
        # Unload details: ownership, groups, etc.:
        roi.unloadDetails()
        # Add externalInfo if exisits to inform PathViewer that it is
        # a PathViewer created ROI (no popup):
        if externalInfo is not None:
            externalInfo.id = None
            externalInfo.unloadDetails()
            details = omero.model.DetailsI()
            details.setExternalInfo(externalInfo)
            roi._details = details
        # Unload source image info:
        roi.unloadImage()
        # Link ROI to target image:
        roi.setImage(target_image)
        # Copy shapes beloning to the ROI:
        for shape in roi.copyShapes():
            shape.id = None
            shape.unloadDetails()
    return results


def copy_rois(conn, source_image_id, target_image_id):
    '''
    This method asks for a copy of source image ROIs
    and saves them to the server
    '''
    rois_to_copy = get_rois_copy(conn, source_image_id, target_image_id)
    rois_to_copy = conn.getUpdateService().saveAndReturnArray(rois_to_copy)
    return "Copied %i ROIs" % len(rois_to_copy)


def run_as_omero_script():
    client = scripts.client(
        'Copy_ROIs.py',
        """
        This script creates map annotations.
        """,
        scripts.Long(
            "Source_Image_Id", optional=False, grouping="1",
            description="Source image Id"),
        scripts.Long(
            "Target_Image_Id", optional=False, grouping="2",
            description="Source image Id"),
        version="0.1",
        authors=["Emil Rozbicki"],
        institutions=["Glencoe Software Inc."],
        contact="emil@glencoesoftware.com",
    )
    try:
        # process the list of args above.
        script_params = {}
        for key in client.getInputKeys():
            if client.getInput(key):
                script_params[key.lower()] = client.getInput(key, unwrap=True)
        # wrap client to use the Blitz Gateway
        conn = BlitzGateway(client_obj=client)

        # get image ids
        source_image_id = script_params["source_image_id"]
        target_image_id = script_params["target_image_id"]
        LOGGER.info(
            "Copying ROIs from Image %i to image %i" %
            (source_image_id, target_image_id))
        # copy images
        message = copy_rois(conn, source_image_id, target_image_id)

        # set ouput message in OMERO.web client
        client.setOutput("Message", rstring(message))
    finally:
        client.closeSession()


def main():
    '''

    OMERO.scripts are executed as ./script so will take advatage of that to
    make the code usable as OMERO.script and standalone.

    '''
    level = logging.INFO
    logging.basicConfig(level=level, format=LOGGING_FORMAT, stream=sys.stdout)
    if not OMERO_IMPORTED:
        LOGGER.warn("OMERO not on the path.")
    if sys.argv[0] == './script':
        run_as_omero_script()
    else:
        # Do somthing else here: parse command line args, etc.
        pass


if __name__ == "__main__":
    main()
