// 搜索or whatever，把要删除的微博筛选出来，然后把下面脚本全部丢进console执行

async function removeWeibo(mid) {
    const formData = new FormData();
    formData.append('mid', mid);
    return fetch('/aj/mblog/del?ajwvr=6', {
        body: formData,
        method: 'post',
        credentials: 'same-origin'
    });
}

async function wait(second) {
    return new Promise((resolve) => {
        setTimeout(resolve, second*1000);
    });
}

async function batchRemoveWeibo() {
    const posts = Array.from(document.querySelectorAll('div[mid]'));
    for( post of posts ) {
        const mid = Number(post.getAttribute('mid'));
        const r = await removeWeibo(mid);
        console.log(`${mid} removed`);
        await wait(1);
    }
    location.reload();
}

batchRemoveWeibo();