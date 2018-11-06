const express = require('express');
const fs = require('fs');
const path = require('path');

const router = express.Router();

/* GET home page. */
router.get('/meta', function(req, res, next) {
  const metadata = fs.readFileSync(path.join(__basedir, 'data/ttf-meta.json'));
  console.log(__dirname);
  res.send(metadata);

});

/* GET home page. */
router.get('/meta/:id', function(req, res, next) {
  const metadata = fs.readFileSync('../');


});

module.exports = router;
