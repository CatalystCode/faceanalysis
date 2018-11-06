const express = require('express');
const router = express.Router();
const provider = require('../providers/metadataprovider');


/* GET all case metadata. */
router.get('/metadata', function(req, res, next) {
  provider.getmetadata((err, metatdata) => {
    if( err ) {
      throw err;
    } else {
      res.send(metatdata);
    }
  })
});

/* GET case metadata by id. */
router.get('/metadata/:id', function(req, res, next) {
  provider.getmetadatabyid(req.params.id, (err, metatdata) => {
    if( err ) {
      throw err;
    } else {
      res.send(metatdata);
    }
  })
});

module.exports = router;
