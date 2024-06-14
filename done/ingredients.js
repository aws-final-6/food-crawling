function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchMaterialDataBatch(start, end, batchSize, delay, callback) {
    let dataArray = [];
    let currentStart = start;

    async function processBatch() {
        let batchEnd = Math.min(currentStart + batchSize - 1, end);
        let completedRequests = 0;

        for (let seq = currentStart; seq <= batchEnd; seq++) {
            $.ajax({
                type: "GET",
                url: "/bbs/ajax.html?q_mode=getMaterialContents&seq=" + seq + "&recipe_seq=6856668",
                dataType: 'json',
                success: function(json) {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(json['html'], 'text/html');

                    const data = {
                        material_number: seq,
                        mname: json['mname'] || '',
                        image: (doc.querySelector('.ingredient_top .ingredient_pic') ? doc.querySelector('.ingredient_top .ingredient_pic').style.background : '').replace('url(','').replace(') center no-repeat; background-size:cover;','') || '',
                        title: doc.querySelector('.ingredient_top .ingredient_tit') ? doc.querySelector('.ingredient_top .ingredient_tit').innerText : '',
                        season: doc.querySelector('.ingredient_info tr:nth-child(1) td') ? doc.querySelector('.ingredient_info tr:nth-child(1) td').innerText : '',
                        storage_temp: doc.querySelector('.ingredient_info tr:nth-child(2) td') ? doc.querySelector('.ingredient_info tr:nth-child(2) td').innerText : '',
                        calories: doc.querySelector('.ingredient_info tr:nth-child(3) td') ? doc.querySelector('.ingredient_info tr:nth-child(3) td').innerText : '',
                        matching_food: doc.querySelector('.ingredient_info tr:nth-child(4) td') ? doc.querySelector('.ingredient_info tr:nth-child(4) td').innerText : '',
                        non_matching_food: doc.querySelector('.ingredient_info tr:nth-child(5) td') ? doc.querySelector('.ingredient_info tr:nth-child(5) td').innerText : '',
                        efficacy: doc.querySelectorAll('.ingredient_cont_tag a').length > 0 ? Array.from(doc.querySelectorAll('.ingredient_cont_tag a')).map(tag => tag.innerText).join(', ') : '',
                        purchase_tip: doc.querySelector('.ingredient_cont:nth-of-type(2) dd') ? doc.querySelector('.ingredient_cont:nth-of-type(2) dd').innerText : '',
                        cleaning_tip: doc.querySelector('.ingredient_cont:nth-of-type(3) dd') ? doc.querySelector('.ingredient_cont:nth-of-type(3) dd').innerText : '',
                        cooking_tip: doc.querySelector('.ingredient_cont:nth-of-type(4) dd') ? doc.querySelector('.ingredient_cont:nth-of-type(4) dd').innerText : '',
                        storage_tip: doc.querySelector('.ingredient_cont:nth-of-type(5) dd') ? doc.querySelector('.ingredient_cont:nth-of-type(5) dd').innerText : ''
                    };

                    dataArray.push(data);
                    completedRequests++;

                    if (completedRequests === (batchEnd - currentStart + 1)) {
                        currentStart = batchEnd + 1;
                        if (currentStart <= end) {
                            processBatch();
                        } else {
                            callback(dataArray);
                        }
                    }
                },
                error: function(xhr, status, error) {
                    console.error("Ajax request failed for seq:", seq, status, error);
                    const data = {
                        material_number: seq,
                        mname: '',
                        image: '',
                        title: '',
                        season: '',
                        storage_temp: '',
                        calories: '',
                        matching_food: '',
                        non_matching_food: '',
                        efficacy: '',
                        purchase_tip: '',
                        cleaning_tip: '',
                        cooking_tip: '',
                        storage_tip: ''
                    };
                    dataArray.push(data);
                    completedRequests++;
                    if (completedRequests === (batchEnd - currentStart + 1)) {
                        currentStart = batchEnd + 1;
                        if (currentStart <= end) {
                            processBatch();
                        } else {
                            callback(dataArray);
                        }
                    }
                }
            });

            // 요청 사이에 딜레이 추가
            await sleep(delay);
        }
    }

    processBatch();
}

function convertToCSV(data) {
    const array = [Object.keys(data[0])].concat(data);

    return array.map(row => {
        return Object.values(row).map(value => {
            return typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value;
        }).join(',');
    }).join('\n');
}

function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], { type: 'text/csv' });
    const downloadLink = document.createElement('a');

    downloadLink.download = filename;
    downloadLink.href = window.URL.createObjectURL(csvFile);
    downloadLink.style.display = 'none';

    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

function saveAllMaterialsToCSV(start, end, batchSize, delay) {
    fetchMaterialDataBatch(start, end, batchSize, delay, function(dataArray) {
        const csv = convertToCSV(dataArray);
        downloadCSV(csv, 'materials_data.csv');
    });
}

// 예시로 1번부터 3509번까지의 데이터를 배치 사이즈 100과 딜레이 500ms로 저장
saveAllMaterialsToCSV(1, 3509, 100, 500);
