import React from 'react';
import ReactDOM from 'react-dom';
import axios from 'axios';

class FaceNetDisplay extends React.Component {
    constructor(props) {
        super(props);
        this.baseUrl = "http://" + process.env.REACT_APP_HOST_MACHINE;
        this.state = {
            originalImgs: [],
            croppedImgs: [],
            croppedMatchedImgs: [],
            croppedMatchedImgsDistances: [],
            originalMatchedImgs: [],
            selectedOriginalImg: null,
            selectedCroppedImg: null,
            selectedMatchedImg: null,
        };
    }

    updateImages(displayType, state) {
        console.log('update images called with: ' + displayType + ' ' + state);
        let imgsPath;
        if (displayType == "original") {
            imgsPath = '/api/cropped_images' + '/' + state.selectedOriginalImg;
        } else if (displayType == "cropped") {
            imgsPath = '/api/cropped_image_matches' + '/' + state.selectedCroppedImg;
        } else if (displayType == "matched") {
            imgsPath = '/api/original_images' + '/' + state.selectedMatchedImg;
        }

        let newState = Object.assign({}, state);
        axios.get(this.baseUrl + imgsPath)
             .then(res => {
                 if (displayType == "original") {
                    newState.croppedImgs = res.data.imgs;
                 } else if (displayType == "cropped") {
                    newState.croppedMatchedImgs = res.data.imgs;
                    newState.croppedMatchedImgsDistances = res.data.distances;
                 } else if (displayType == "matched") {
                    newState.originalMatchedImgs = res.data.imgs;
                 }
                 console.log("the new state");
                 console.log(newState);
                 this.setState(newState);
        });
    }

    handleImgClick(img, displayType) {
        console.log("IMAGE SELECTED: " + img + " DISPLAY TYPE: " + displayType);
        let newState = Object.assign({}, this.state);
        if (displayType == "original") {
            newState.selectedOriginalImg = img;
            newState.selectedCroppedImg = null;
            newState.selectedMatchedImg = null;
            newState.croppedImgs = [];
            newState.croppedMatchedImgs = [];
            newState.originalMatchedImgs = [];
            newState.croppedMatchedImgsDistances = [];
        } else if (displayType == "cropped") {
            newState.selectedCroppedImg = img;
            newState.selectedMatchedImg = null;
            newState.croppedMatchedImgs = [];
            newState.originalMatchedImgs = [];
        } else if (displayType == "matched") {
            newState.selectedMatchedImg = img;
            newState.originalMatchedImgs = [];
        }
        this.updateImages(displayType, newState);
    }

    loadOriginalData() {
        console.log("loadOriginalData called");
        let imgsPath = '/api/original_images';
        let newState = Object.assign({}, this.state);
        var that = this;
        axios.get(this.baseUrl + imgsPath)
             .then(res => {
                 newState.originalImgs = res.data.imgs;
                 that.setState(newState);
                 console.log("NEW STATE SET");
                 console.log(that.state);
                 console.log(newState);
        });
    }

    componentDidMount() {
        this.loadOriginalData();
    }

    render() {
        let croppedImgPath = '/static/cropped_image';
        let originalImgPath = '/static/original_image';

        let noImgClicked= this.state.selectedOriginalImg == null;
        let originalImgClicked = this.state.selectedOriginalImg != null && this.state.selectedCroppedImg == null;
        let croppedImgClicked = this.state.selectedOriginalImg != null && this.state.selectedCroppedImg != null && this.state.selectedMatchedImg == null;
        let croppedMatchedImgClicked = this.state.selectedOriginalImg != null && this.state.selectedCroppedImg != null && this.state.selectedMatchedImg != null;
        
        let imgListDisplays = [
            <ImageListDisplay baseUrl={this.baseUrl} imgs={this.state.originalImgs} imgPath={originalImgPath} title={'Original Images'} imgOnClick={this.handleImgClick.bind(this)} displayType={'original'} distances={[]} />,
            <ImageListDisplay baseUrl={this.baseUrl} imgs={this.state.croppedImgs} imgPath={croppedImgPath} title={'Cropped Images'} imgOnClick={this.handleImgClick.bind(this)} displayType={'cropped'} distances={[]} />,
            <ImageListDisplay baseUrl={this.baseUrl} imgs={this.state.croppedMatchedImgs} imgPath={croppedImgPath} title={'Cropped Matches'} imgOnClick={this.handleImgClick.bind(this)} displayType={'matched'} distances={this.state.croppedMatchedImgsDistances} />,
            <ImageListDisplay baseUrl={this.baseUrl} imgs={this.state.originalMatchedImgs} imgPath={originalImgPath} title={'Original Match'} imgOnClick={this.handleImgClick.bind(this)} displayType={'original_matched'} distances={[]} />
        ];

        let page;
        if (noImgClicked) {
            page = (
                <div>
                    <UploadImageDisplay baseUrl={this.baseUrl} onPollPending={this.loadOriginalData.bind(this)}/>
                    {imgListDisplays[0]}
                </div>
            );
        
        } else if (originalImgClicked) {
            page = (
                <div>
                    <UploadImageDisplay baseUrl={this.baseUrl} onPollPending={this.loadOriginalData.bind(this)}/>
                    {imgListDisplays[0]}
                    {imgListDisplays[1]}
                </div>
            );
        } else if (croppedImgClicked) {
            page = (
                <div>
                    <UploadImageDisplay baseUrl={this.baseUrl} onPollPending={this.loadOriginalData.bind(this)}/>
                    {imgListDisplays[0]}
                    {imgListDisplays[1]}
                    {imgListDisplays[2]}
                </div>
            ); 
        } else if (croppedMatchedImgClicked) {
            page = (
                <div>
                    <UploadImageDisplay baseUrl={this.baseUrl} onPollPending={this.loadOriginalData.bind(this)}/>
                    {imgListDisplays[0]}
                    {imgListDisplays[1]}
                    {imgListDisplays[2]}
                    {imgListDisplays[3]}
                </div>
            );
        }

        return page;
    }
}

class ImageListDisplay extends React.Component {

    handleImgClick(img) {
        if (this.props.displayType != 'original_matched') {
            this.props.imgOnClick(img, this.props.displayType);
        }
    }

    render() {
        let imgRows = [];
        let rowCount = 0;
        let imgs = this.props.imgs;
        let distances = this.props.distances;
        for (let i = 0; i < imgs.length; i++) {
            if (i % 3 == 0) {
                imgRows.push([]);
                if (i != 0) {
                    rowCount++;
                }
            }
            let distanceHeader = distances.length > 0 ? <h3>Distance: {distances[i]}</h3> : null;
            let imgThumbnail = (
                <div className="col-md-4" key={i}>
                    <a href="javascript:void(0);" onClick={() => this.handleImgClick(imgs[i])}>
                        <img src={this.props.baseUrl + this.props.imgPath + '/' + imgs[i] + ".jpg"} className="img-responsive thumbnail" style={{width:"100%", height:"100%"}}></img>
                    </a>
                    {distanceHeader}
                </div>
            ); 
            imgRows[rowCount].push(imgThumbnail);
        }

        let rowDivs = [];
        for (let i = 0; i < imgRows.length; i++) {
            rowDivs.push(<div key={i} className="row">{imgRows[i]}</div>);
        }

        return (
            <div>
                <h1>{this.props.title}:</h1>
                {rowDivs}
            </div>
        );
    }
}

class UploadImageDisplay extends React.Component {
    
	constructor(props) {
		super(props);
        this.interval = null;
		this.state = {
			file: null,
		};
	}

    pollPendingImage() {
        console.log("poll pending image called");
        console.log("file name!!:", this.state.file)
        let filename = this.state.file.name;
        let img_id = filename.slice(0, filename.length - 4);
        var that = this;
        axios.get(this.props.baseUrl + '/api/upload_image/' + img_id)
             .then(res => {
                 if (res.data.finished_processing == true) {
                    console.log("poll pending image finished_processing true");
                    that.props.onPollPending();
                    clearInterval(that.interval);
                 } else {
                     console.log("poll pending image finished_processing not done");
                 }
        });
    }
    
    handleSubmit(e) {
        e.preventDefault();
		
		if (this.state.file != null) {
			var formData = new FormData();
			formData.append("file", this.state.file);
            var that = this;
			axios.post(this.props.baseUrl + '/api/upload_image/', formData, {
    			headers: {
      				'Content-Type': 'multipart/form-data'
   				}
			}).then(function(response) {
               console.log("RESPONSE FROM POST: ", response);
               that.pollPendingImage();
               that.interval = setInterval(function() {that.pollPendingImage();}, 2000); 
            });
            
            ;
		}
    }

	handleImageChange(e) {
		let file = e.target.files[0];
		this.setState({
			file: file,
		});
	}

    render() {
        return (
            <div>
            	<form onSubmit={(e) => this.handleSubmit(e)}>
  					<input name="file" type="file" onChange={(e) => this.handleImageChange(e)} />
  					<input type="submit" value="Upload" />
				</form>
			</div>
        );
    }
}

ReactDOM.render(
  <FaceNetDisplay />,
  document.getElementById('root')
);
