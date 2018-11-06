import { ActionWithPayload, ImageProperties } 
  from '../constants';
import { ADD_IMAGE, SET_SUBJECT, SET_TARGET, CLEAR_CANDIDATES  } 
  from '../constants';

const initialState = {
  subjectImage: {} as ImageProperties,
  targetImage: {} as ImageProperties,
  candidateImages: {} as ImageProperties[]
};

const rootReducer = (state = initialState, action: ActionWithPayload<ImageProperties>  ) => {
  switch (action.type){
    case ADD_IMAGE:
      state.candidateImages.push(action.payload);
      return state;
    case SET_SUBJECT:
      state.subjectImage = action.payload;
      return state;
    case SET_TARGET:
      state.targetImage = action.payload;
      return state;
    case CLEAR_CANDIDATES:
      state.candidateImages = [];
      return state;

    default:
      return state;
  }
};

export default rootReducer;