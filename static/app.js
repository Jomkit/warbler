function updateNumLikes(){
    let numLikes = $('.btn-primary').length;
    $('#likes')[0].text = numLikes;
    return;
}

async function handleLikes(evt){
    evt.preventDefault();
    if(evt.target.tagName == 'BUTTON'){
        let msgId = $(this).attr('id');
        await $.post(`/messages/${msgId}/like`);

        evt.target.classList.toggle('btn-primary');
        evt.target.classList.toggle('btn-secondary');
        updateNumLikes();
    }
    return;
}
$('#messages-form button').on('click', handleLikes)

async function showNewMessage(evt){
    evt.preventDefault();
    
    await $.get('/messages/new', function( data ){
        $('.modal-half').html(data);
    });
    return;
}

$('#new-msg-link').on('click', showNewMessage);

async function postNewMessage(e){
    if(e.target.id === "submit-new-post"){
        e.preventDefault();
        
        $.post('/messages/new', $( "#new-msg-form" ).serialize() );

        $('#close-new-msg-form').trigger("click");
        location.reload(true);

        return;
    }
}
$('.new-msg-form').on('click', postNewMessage);