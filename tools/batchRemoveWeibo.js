// 这个脚本用于在微博页面上批量删除微博
// 先在页面中搜索，把要删除的微博筛选出来，然后把下面脚本全部丢进 console 执行，凡是在当前页面上的微博都会被删除

async function removeWeibo(mid) {
    const formData = new FormData();
    formData.append('mid', mid);
    await fetch('/aj/mblog/del?ajwvr=6', {
        body: formData,
        method: 'post',
        credentials: 'same-origin'
    });
}

function wait(seconds) {
    return new Promise(resolve => setTimeout(resolve, seconds * 1000));
}

async function batchRemoveWeibo() {
    const mids = Array.from(document.querySelectorAll('div[mid]'), post => post.getAttribute('mid'))
        .filter(Boolean);
    for (const mid of new Set(mids)) {
        await removeWeibo(mid);
        console.log(`${mid} removed`);
        await wait(1);
    }
    location.reload();
}

batchRemoveWeibo();
