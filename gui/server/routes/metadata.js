const express = require('express');
const fs = require('fs');
const path = require('path');
const provider = require('../providers/metadataprovider');
const router = express.Router();

/* GET home page. */
router.get('/meta', function (req, res, next) {
  const metadata = fs.readFileSync(path.join(__basedir, 'data/ttf-meta.json'));
  console.log(__dirname);
  res.send(metadata);
})

/* GET all case metadata. */
router.get('/', function (req, res, next) {
  provider.getmetadata((err, metatdata) => {
    if (err) {
    } else {
      console.log(metatdata);
    }
  })
});

/* GET case metadata by id. */
router.get('/:id', function (req, res, next) {
  provider.getmetadatabyid(req.params.id, (err, metatdata) => {
    if (err) {
    } else {
      console.log(metatdata);
    }
  })
});

module.exports = router;
