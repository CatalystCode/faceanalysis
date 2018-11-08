import { applyMiddleware, createStore } from 'redux';
import thunk from 'redux-thunk'
import Raven from 'raven-js';
import reducers from './reducers';
// import axios from 'axios';
// TODO: git@github.com:pkellner/pluralsight-course-react-aspnet-core.git
export function getDefaultMiddleware() {
    return [thunk, logger, crashReporter]
}

export const configureStore = (initialState = {}) => {
    return createStore(
        reducers,
        initialState,
        applyMiddleware(logger, crashReporter)
    );
}


const logger = store => next => action => {
    console.log('dispatching', action)
    let result = isPlainObject(action) ? next(action) : 'an object ';
    console.log('next state', store.getState())
    return result
}

const crashReporter = store => next => action => {
    try {
        return isPlainObject(action) ? next(action) : 'an object ';
    } catch (err) {
        console.warn('Caught an exception!', err)
        Raven.captureException(err, {
            extra: {
                action,
                state: store.getState()
            }
        })
        //throw err
    }
}

/**
 * @param {any} obj The object to inspect.
 * @returns {boolean} True if the argument appears to be a plain object.
 */
const isPlainObject = (obj) => {
    if (typeof obj !== 'object' || obj === null) return false

    let proto = obj
    while (Object.getPrototypeOf(proto) !== null) {
        proto = Object.getPrototypeOf(proto)
    }

    return Object.getPrototypeOf(obj) === proto
}
