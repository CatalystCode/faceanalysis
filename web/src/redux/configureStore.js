import { applyMiddleware, createStore } from 'redux';
import Raven from 'raven-js';
import reducers from './reducers';
// import axios from 'axios';
// TODO: git@github.com:pkellner/pluralsight-course-react-aspnet-core.git

export const configureStore = (initialState = {}) => {

    // const restUrl = 'http://localhost:3000/api';
    // const client = axios.create({
    //     baseURL: restUrl,
    //     //responseType: 'json'
    // });

    return createStore(
        reducers,
        initialState,
        applyMiddleware(logger, crashReporter)
        // composeEnhancers(
        //     applyMiddleware(...middleware))" */
    );
}


const logger = store => next => action => {
    console.log('dispatching', action)
    let result = next(action)
    console.log('next state', store.getState())
    return result
}

const crashReporter = store => next => action => {
    try {
        return next(action)
    } catch (err) {
        console.error('Caught an exception!', err)
        Raven.captureException(err, {
            extra: {
                action,
                state: store.getState()
            }
        })
        throw err
    }
}

