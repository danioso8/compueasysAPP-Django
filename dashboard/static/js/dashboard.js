
function openEditModal(id, username, email) {
    document.getElementById('editModal').style.display = 'block';
    document.getElementById('modal_user_id').value = id;
    document.getElementById('modal_username').value = username;
    document.getElementById('modal_email').value = email;
}
function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}
window.onclick = function(event) {
    var modal = document.getElementById('editModal');
    if (event.target == modal) {
        closeEditModal();
    }
}
