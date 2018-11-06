const express = require('express');
const fs = require('fs');
const path = require('path');
const provider = require('../providers/metadataprovider');
const router = express.Router();

const metadataFile = './gui/server/data/ttf-meta.json';

/* GET all case metadata. */
router.get('/', function(req, res, next) {
  provider.getmetadata((err, metatdata) => {
    if( err ) {
    } else {
      console.log(metatdata);
    }
  })
});

/* GET case metadata by id. */
router.get('/:id', function(req, res, next) {
  provider.getmetadatabyid(req.params.id, (err, metatdata) => {
    if( err ) {
    } else {
      console.log(metatdata);
    }
  })
});

module.exports = router;
