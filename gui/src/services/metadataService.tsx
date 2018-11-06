

export const getAll = () => {
    fetch('/metadata')
    .then( (response) => {
        ;
    })
    .catch ( (reason) =>{
        console.log(reason)
    })
    // return { "metadata": "foobar"};
}

export const get = (id: string) => {
    fetch(`/metadata/${id}`)
    .then( (response) => {
        console.log(response);
    })
    .catch ( (reason) =>{
        console.log(reason);
        
    })
    // return { "metadata": "foobar"};;
}