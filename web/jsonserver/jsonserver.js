// run by typing node jsonserver
const path = require('path');
const jsonServer = require('json-server');
const server = jsonServer.create();
const router = jsonServer.router(path.join(__dirname, 'ttf-db.json'));
const middlewares = jsonServer.defaults();
server.use(function(req, res, next) {
    setTimeout(next, 1000);
});
server.use(middlewares);
server.use('/api', router);
const port = 3001
server.listen(port, () => {
    console.log(`JSON Server is running on port ${port}`);
});