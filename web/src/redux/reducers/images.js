import { ADD_IMAGE, SHOW_IMAGE, SET_SUBJECT, SET_TARGET, CLEAR_CANDIDATES } from '../actions/images';

export function images(
  state = {
    data: [],
    errorMessage: ''
  }, action) {
  switch (action.type) {
    case ADD_IMAGE:
      return Object.assign({}, state,
        action.payload.data);
    case SHOW_IMAGE:
    case SET_SUBJECT:
      return {
        ...state,

      }
    case SET_TARGET:
    case CLEAR_CANDIDATES:
    default:
      return state;
  }
}
