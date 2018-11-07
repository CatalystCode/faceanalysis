import {createStore} from 'redux';
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
        initialState /*",
        composeEnhancers(
            applyMiddleware(...middleware))" */
    );
}