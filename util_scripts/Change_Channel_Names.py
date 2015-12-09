# -*- coding: utf-8 -*-
"""
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
"""

import omero
from omero.gateway import BlitzGateway
from omero.rtypes import rstring, rlong
import omero.scripts as scripts

import random


class renameChannels:

    def __init__(self, conn, scriptParams):
        """
        Class rename channels in an object defined in scriptParams by
        "Data_Type", a list of object "IDs" and "New_Channel_Names".
        source dataset "IDS".
        @param conn: BlitzGateway connector
        @param scriptParams: scipt parameters.
        """
        self.conn = conn
        self.lc_paging = 100
        self.image_paging = 100
        self.data_type = scriptParams["Data_Type"]
        self.ids = scriptParams["IDs"]
        self.new_channel_names = scriptParams["New_Channel_Names"]
        self.image_id_list = []
        self.query_service = self.conn.getQueryService()
        self.update_service = self.conn.getUpdateService()
        self.get_image_ids_query = \
            "select distinct i.id from Image i" \
            " left outer join i.pixels as p" \
            " left outer join p.channels as c" \
            " join c.logicalChannel as lc" \
            " where lc.id in (:ids)"
        self.get_image_query = \
            "select i from Image i" \
            " left outer join fetch i.pixels as p" \
            " left outer join fetch p.channels as c" \
            " join fetch c.logicalChannel as lc" \
            " where i.id in (:ids)"
        self.well_query = "select distinct lc.id" \
            " from Well as w" \
            " join w.wellSamples as ws" \
            " join ws.image as i" \
            " join i.pixels as pixels" \
            " join pixels.channels as c" \
            " join c.logicalChannel as lc" \
            " where w.id in (:ids)"
        self.plate_query = "select distinct lc.id" \
            " from Plate as p" \
            " join p.wells as w" \
            " join w.wellSamples as ws" \
            " join ws.image as i" \
            " join i.pixels as pixels" \
            " join pixels.channels as c" \
            " join c.logicalChannel as lc" \
            " where p.id in (:ids)"
        self.screen_query = \
            "select distinct lc.id" \
            " from Screen as s" \
            " join s.plateLinks as p_link" \
            " join p_link.child as p" \
            " join p.wells as w" \
            " join w.wellSamples as ws" \
            " join ws.image as i" \
            " join i.pixels as pixels" \
            " join pixels.channels as c" \
            " join c.logicalChannel as lc" \
            " where s.id in (:ids)"
        self.dataset_query = \
            "select distinct lc.id" \
            " from Dataset as d" \
            " join d.imageLinks as dil" \
            " join dil.child as i" \
            " join i.pixels as pixels" \
            " join pixels.channels as c" \
            " join c.logicalChannel as lc" \
            " where d.id in (:ids)"
        self.project_query = \
            "select distinct lc.id" \
            " from Project p" \
            " join p.datasetLinks as links" \
            " join links.child as dataset" \
            " join dataset.imageLinks as dil" \
            " join dil.child as i" \
            " join i.pixels as pixels" \
            " join pixels.channels as c" \
            " join c.logicalChannel as lc" \
            " where p.id in (:ids)"
        self.image_query = \
            "select distinct lc.id" \
            " from Image as i" \
            " join i.pixels as pixels" \
            " join pixels.channels as c" \
            " join c.logicalChannel as lc" \
            " where i.id in (:ids)"

    def getLcIdsList(self, query):
        params = omero.sys.ParametersI()
        params.addIds(self.ids)
        lc_ids = self.query_service.projection(query, params)
        if len(lc_ids) == 0:
            return None
        lc_ids = [lc_id[0] for lc_id in lc_ids]
        return [lc_id.getValue() for lc_id in lc_ids]

    def updateImageNames(self, image_list):
        image_list = self.update_service.saveAndReturnArray(image_list)

    def removeLCsFromList(self, image, lc_ids_list):
        image_noc = image.getPrimaryPixels().getSizeC().getValue()
        for c in range(image_noc):
            lc_id = image.getPrimaryPixels().getChannel(c). \
                getLogicalChannel().getId().getValue()
            try:
                lc_ids_list.remove(lc_id)
            except ValueError:
                print '\tWARN: %s not in the list' % lc_id
        return lc_ids_list

    def renameLCs(self, image):
        number_of_channels = len(self.new_channel_names)
        for c in range(number_of_channels):
            image.getPrimaryPixels().getChannel(c).getLogicalChannel().setName(
                rstring(self.new_channel_names[c]))

    def renameBatch(self, lc_ids, step):
        lc_ids_batch = random.sample(lc_ids, step)
        params = omero.sys.ParametersI()
        params.addIds(lc_ids_batch)
        number_of_channels = len(self.new_channel_names)
        paging = self.image_paging
        counter = 0
        while len(lc_ids_batch) > 0:
            params.page(counter * paging, paging)
            counter += 1
            image_ids = query_service.projection(
            get_image_ids_query, params, ctx)
            image_ids = [image_ids[0].val for image_ids in image_ids]
            image_list_params = omero.sys.ParametersI()
            image_list_params.addIds(image_ids)
            image_list = self.query_service.findAllByQuery(
                self.get_image_query, params)
            print "Retrived %i images" % len(image_list)
            for image in image_list:
                check_lc = image.getPrimaryPixels().getChannel(0). \
                    getLogicalChannel().getId().getValue()
                if check_lc not in lc_ids:
                    self.updateImageNames(image_list)
                    return
                print "Renaming", image.getName().getValue(), \
                    image.getId().getValue()
                image_noc = image.getPrimaryPixels().getSizeC().getValue()
                if image_noc != number_of_channels:
                    print "\tChannels don't match, skipping"
                    lc_ids = self.removeLCsFromList(image, lc_ids)
                    lc_ids_batch = self.removeLCsFromList(image, lc_ids_batch)
                    continue
                self.renameLCs(image)
                print 'Clearing full lc list.'
                lc_ids = self.removeLCsFromList(image, lc_ids)
                print 'Clearing batch list.'
                lc_ids_batch = self.removeLCsFromList(image, lc_ids_batch)
            self.updateImageNames(image_list)

    def renameImages(self, lc_ids):
        step = self.lc_paging
        print "Got %i unique logical channels" % len(lc_ids)
        while len(lc_ids) > 0:
            if len(lc_ids) < 100:
                step = len(lc_ids)
            self.renameBatch(lc_ids, step)
            print "\n%i unique logical channels remains" % len(lc_ids)

    def getQuery(self):
        if self.data_type == "Screen":
            return self.screen_query
        elif self.data_type == "Plate":
            return self.plate_query
        elif self.data_type == "Well":
            return self.well_query
        elif self.data_type == "Project":
            return self.project_query
        elif self.data_type == "Dataset":
            return self.dataset_query
        elif self.data_type == "Image":
            return self.image_query
        else:
            print ""

    def run(self):
        query = self.getQuery()
        if query == "":
            return "Object type not supported."
        lc_ids = self.getLcIdsList(query)
        if lc_ids is None:
            return "No images to rename."
        self.renameImages(lc_ids)
        return "Done"


def runAsScript():
    """
    The main entry point of the script, as called by the client via the
    scripting service, passing the required parameters.
    """

    dataTypes = [
        rstring('Project'), rstring('Dataset'), rstring('Image'),
        rstring('Well'), rstring('Plate'), rstring('Screen')]

    client = scripts.client(
        'Change_Channel_Names.py',
        """Rename channel Names for a given object.""",

        scripts.String(
            "Data_Type", optional=False, grouping="1",
            description="Choose source of images",
            values=dataTypes, default="Dataset"),

        scripts.List(
            "IDs", optional=False, grouping="2",
            description="List of object IDs"
            " Plates.").ofType(rlong(0)),

        scripts.List(
            "New_Channel_Names", optional=False, grouping="3",
            description="Comma separated list of the new Channel Names"
        ).ofType(rstring(",")),

        version="0.1",
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

        # wrap client to use the Blitz Gateway
        conn = BlitzGateway(client_obj=client)
        nameChanger = renameChannels(conn, scriptParams)
        message = nameChanger.run()
        client.setOutput("Message", rstring(message))

    finally:
        client.closeSession()

if __name__ == "__main__":
    runAsScript()
