var doc = document;

// 각 페이지 별 구분변수 추가 시작 - 240219
const mainPage = doc.querySelector('#mainPage');
const myThankPage = doc.querySelector('#myThankPage');
const sendTkPage = doc.querySelector('#sendTkPage');
const bestPage = doc.querySelector('#bestPage');
const myTokenPage = doc.querySelector('#myTokenPage');
// 각 페이지 별 구분변수 추가 끝 - 240219

if (mainPage) {
  // 카드 레이아웃 생성 테스트를 위해 제작하였습니다.
  // 자동 생성시 삭제 하셔도 됩니다.
  const testText = `
        <div class="chkCard col-lg-4 col-md-6 mb-2">
          <div class="card cardList">
            <div class="card-body p-3 d-flex justify-content-center align-items-center">
              <div class="d-flex align-items-center">
                <a class="me-2 w-100" style="max-width: 32px;" href="#">
                  <img src="../assets/img/woori.png" class="img-fluid">
                </a>
                <div>
                  <p class="card-title colorCustom_02 m-0 fw-med">은행 브랜드전략부</p>
                  <h6 class="card-text colorCustom_01 fs-6">김문희 <span class="fw-bold colorCustom_03">부부장</span></h6>
                </div>
              </div>
              <span class="mx-2 d-block icon_right_arrow"></span>
              <div class="d-flex align-items-center">
                <a class="me-2 w-100" style="max-width: 32px;" href="#">
                  <img src="../assets/img/woori.png" class="img-fluid">
                </a>
                <div>
                  <p class="card-title colorCustom_02 m-0 fw-med">지주 브랜드전략부</p>
                  <h6 class="card-text colorCustom_01 fs-6">김현철 <span class="fw-bold colorCustom_03">대리</span></h6>
                </div>
              </div>
            </div>
            <div class="card-body px-0 py-3 mx-3" style="border-top:1px solid #14a8ea;">
              <div class="mb-3">
                <a data-bs-toggle="modal" data-bs-target="#card_modal" href="#" class="d-flex">
                  <div class="w-25 h-100 rounded overflow-hidden me-2" style="min-width: 72px;">
                    <img src="../assets/img/photo_card_02.png" class="img-fluid">
                  </div>
                  <div class="overflow-hidden">
                    <p style="min-height: 50px; text-overflow: ellipsis; word-wrap: break-word;
                    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;"
                      class="card-text mb-0 colorCustom_01 fw-med">전략기획부와 ESG팀을 위해 밤낮 고생하시는 부부장님 새해 복 많으시고, 새해에도 잘
                      부탁드립니다!
                    </p>
                    <div class="hash">
                      <span class="badge colorCustom_03 fw-bold"># 마음</span>
                      <span class="badge colorCustom_03 fw-bold"># 행동</span>
                      <span class="badge colorCustom_03 fw-bold"># 지혜</span>
                    </div>
                  </div>
                </a>
              </div>

              <div class="card-body p-0 d-flex justify-content-between">
                <div class="d-flex">
                  <a href="#" class="d-flex heartBtn btn p-0 me-2"><i class="me-1"></i><span
                      class="fw-med colorCustom_01">1</span></a>
                  <a href="#" class="d-flex commentBtn btn p-0" data-bs-toggle="modal"
                    data-bs-target="#comment_modal"><i class="me-1"></i><span class="fw-med colorCustom_01">2</span></a>
                </div>
                <div class="position-relative">
                  <a href="#" class="btn p-0 me-1 fw-med colorCustom_01"
                    style="cursor:default;"><span>2024-02-06</span></a>
                  <button class="btn p-0 editBtn" type="button" id="conversionRate" data-bs-toggle="dropdown"
                    aria-haspopup="true" aria-expanded="false">
                    <span class="d-block"></span>
                  </button>
                  <div class="dropdown-menu dropdown-menu-end" aria-labelledby="conversionRate"
                    data-popper-placement="bottom-end"
                    style="position: absolute; inset: 0px 0px auto auto; margin: 0px; transform: translate(0px, 25px);">
                    <a class="dropdown-item" href="javascript:void(0);" data-bs-toggle="modal" data-bs-target="#editCard">수정하기</a>
                    <a class="dropdown-item" href="/praiseDelete/72999" onclick="return confirmDelete()">삭제하기</a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
`

  // 카드 레이아웃 생성 테스트를 위해 제작하였습니다.
  // 자동 생성시 삭제 하셔도 됩니다.
  const cardsPerPage = 9;
  const cardListNum = 50;
  const cardWrap = doc.querySelector('#cardWrap');
  const moreBtn = doc.querySelector('#moreBtn');

  for (let i = 0; i < cardsPerPage; i++) {
    cardWrap.innerHTML += testText;
  }

  function loadMoreCards() {
    const currentCards = doc.querySelectorAll('.chkCard');
    const currentCardCount = currentCards.length;

    if (currentCardCount < cardListNum) {
      const remainingCards = Math.min(cardsPerPage, cardListNum - currentCardCount);
      for (let i = 0; i < remainingCards; i++) {
        cardWrap.innerHTML += testText;
      }
    }
  }

  // "더보기" 버튼에 클릭 이벤트 추가 시작
  moreBtn.addEventListener('click', (e) => {
    e.preventDefault();
    loadMoreCards();
    callBtnFunc();
  });
  // "더보기" 버튼에 클릭 이벤트 추가 끝


  function callBtnFunc() {
    const allHeartBtn = doc.querySelectorAll('.heartBtn');
    const allCommentBtn = doc.querySelectorAll('.commentBtn');

    allHeartBtn.forEach((btn, btnIndex) => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const currentCount = parseInt(btn.querySelector('span').innerHTML, 10) || 0;

        if (btn.querySelector('i').classList.contains('clicked')) {
          btn.querySelector('i').classList.remove('clicked');
          btn.querySelector('span').innerHTML = currentCount - 1;
        } else {
          btn.querySelector('i').classList.add('clicked');
          btn.querySelector('span').innerHTML = currentCount + 1;
        }
      });
    });
  }
  callBtnFunc();
}

// 헤더 생성 후 스크립트 시작
// window.onload 코드 삭제 - 240221
// window.onload = function () {
// HOME 페이지, 나의토큰 페이지 수정하기 모달 스와이퍼 시작 - 240219
if (mainPage || myTokenPage) {
  var swiperTopNum = $('.gallery-top').find('.swiper-slide');
  var swiperSubNum = $('.gallery-thumbs').find('.gallery-thumbs');

  var galleryTop = new Swiper('.gallery-top', {
    spaceBetween: 10,
    slidesPerView: 1,
  });

  var galleryThumbs = new Swiper('.gallery-thumbs', {
    slidesPerView: 1,
    spaceBetween: 10,
    navigation: {
      nextEl: '.swiper-button-next',
      prevEl: '.swiper-button-prev',
    },
    slideToClickedSlide: true,
  });

  galleryTop.controller.control = galleryThumbs;
  galleryThumbs.controller.control = galleryTop;

}
// HOME 페이지, 나의토큰 페이지 수정하기 모달 스와이퍼 시작 - 240219


// 헤더 파란색상 배경 위치값 삭제 - 240221
// 헤더 파란색상 배경 끝

//부서, 직위 서브 찾기 탭 생성 시작
const chkHiddenInputs = doc.querySelectorAll('.chkHiddenInput');
doc.addEventListener('click', (event) => {
  const clickedElement = event.target;
  const isChkHiddenInput = clickedElement.classList.contains('chkHiddenInput') || clickedElement.closest('.chkHiddenInput');

  chkHiddenInputs.forEach((item, index) => {
    const editSearchBox = item.querySelector('.editSearchBox');

    if (!isChkHiddenInput || item !== clickedElement.closest('.chkHiddenInput')) {
      editSearchBox.classList.add('d-none');
    } else {
      editSearchBox.classList.remove('d-none');
    }
  });
});
//부서, 직위 서브 찾기 탭 생성 끝

// 하단 모바일 내비게이션바 버튼 색상 시작
const moNavPage = [
  doc.querySelector('#mainPage'),
  doc.querySelector('#myThankPage'),
  doc.querySelector('#sendTkPage'),
  doc.querySelector('#bestPage'),
  doc.querySelector('#myTokenPage'),
]

const allMoMenu = doc.querySelectorAll('.mobile-navigation button');
allMoMenu.forEach((menu, menuIndex) => {
  if (moNavPage[menuIndex]) {
    menu.querySelector('.row > span').style.cssText = `mask-image: url(../assets/img/icon_menu_0${menuIndex+1}_02.svg)`;
  }
});
// 하단 모바일 내비게이션바 버튼 색상 끝



// 검색 아이콘 클릭시 검색 서브 input 탭 닫기 시작
const searchBox = doc.querySelector('.searchBox');
const searchOpenBtn = doc.querySelector('.searchOpenBtn');
searchOpenBtn.addEventListener('click', () => {
  if (searchBox.classList.contains('clicked')) {
    searchBox.classList.remove('clicked');
  } else {
    searchBox.classList.add('clicked');
  }
});

const search = doc.querySelector('.search');
search.addEventListener('click', () => {
  if (searchBox.classList.contains('clicked')) {
    searchBox.classList.remove('clicked');
  }
});
// 검색 아이콘 클릭시 검색 서브 input 탭 닫기 끝
// 헤더 생성 후 스크립트 끝


// 하단 내비게이션 높잇값 만큼 모든 페이지 높이조절 시작

const moNav_h = doc.querySelector('.mobile-navigation').clientHeight;
const allPage = document.querySelector('.allPage');
if (allPage) {
  allPage.style.paddingBottom = moNav_h + 40 + 'px';
}
// 하단 내비게이션 높잇값 만큼 모든 페이지 높이조절 끝

// 공통 js 시작 - 240222
const userProfile = doc.querySelectorAll('.user_profile, .customSize');
if (userProfile) {
  userProfile.forEach(item => {
    const getProfileWidth = item.clientWidth;
    console.log(getProfileWidth);
    item.style.height = getProfileWidth + 'px';
  });
}
// 공통 js 끝 - 240222

if (myThankPage) {
  // 신규 떙큐 톡이 있을 시 숫자 + 원형 배경 아이콘 생성 시작 - 240221
  const new_tk_num = document.querySelectorAll('.new_tk_num span');
  new_tk_num.forEach(item => {
    if (item.textContent.trim() === "") {
      item.style.display = 'none';
    } else {
      item.style.display = 'block';
    }
  });
  // 신규 떙큐 톡이 있을 시 숫자 + 원형 배경 아이콘 생성 끝 - 240221

  // MY땡큐 페이지 대화방 진입시 스크롤 하단 고정 시작 - 240220
  const tkTalkPage = doc.querySelector('.tkTalkPage');
  if (tkTalkPage) {
    window.scrollTo(0, document.body.scrollHeight);
  }
}
// MY땡큐 페이지 대화방 진입시 스크롤 하단 고정 끝 - 240220
// }
// window.onload 코드 삭제 - 240221


if (sendTkPage) {
  const sendSwiperBox = doc.querySelector('.swiperBox');

  var sendCardSwiper = new Swiper('.sendCardSwiper', {
    slidesPerView: 3,
    spaceBetween: 10,

    navigation: {
      nextEl: '.swiperNext',
      prevEl: '.swiperPrev',
    },
    breakpoints: {
      1000: {
        slidesPerView: 10,
      },
      600: {
        slidesPerView: 5,
      },
      400: {
        slidesPerView: 4,
      },
    }
  });

  const sendPhotoBtn = doc.querySelectorAll('.cardOptionBtn button');
  sendPhotoBtn.forEach((btn) => {
    btn.addEventListener('click', () => {
      sendPhotoBtn.forEach((siblingBtn) => {
        siblingBtn.classList.remove('clicked');
      });
      btn.classList.add('clicked');
    });
  });

  const sendCardBox = doc.querySelector('.sendCardSwiper');
  const showPhoto = doc.querySelector('#sendTkPage .showPhoto img');

  sendCardBox.addEventListener('click', event => {
    const clickedPhoto = event.target.closest('.swiper-slide');
    if (!clickedPhoto) return;

    // 칭찬하기 이미지 클릭시 효과 및 보여질 이미지 src 가져오기 시작 - 240219
    const siblings = sendCardBox.querySelectorAll('.swiper-slide');
    siblings.forEach(siblingPhoto => {
      siblingPhoto.classList.remove('picked');
    });

    clickedPhoto.classList.add('picked');
    const imgSrc = clickedPhoto.querySelector('img').getAttribute('src');
    showPhoto.src = imgSrc;
    // 칭찬하기 이미지 클릭시 효과 및 보여질 이미지 src 가져오기 끝 - 240219
  });

  // 칭찬하기 글 초기화 시작 - 240219
  const sendCardReset = doc.querySelector('#sendCardReset');
  sendCardReset.addEventListener('click', () => {
    doc.querySelector('.sendMessage textarea').value = "";
  });
  // 칭찬하기 글 초기화 끝 - 240219
}


if (bestPage) {
  // 우리칭찬왕 버튼 클릭시 CSS 추가 시작 - 240219
  const bestBtnBox = doc.querySelector('.bestBtnBox');

  bestBtnBox.addEventListener('click', event => {
    const clickedBtn = event.target.closest('.bestBtnBox button');
    if (!clickedBtn) return;

    const siblings = doc.querySelectorAll('.bestBtnBox button');
    siblings.forEach(siblingBtn => {
      siblingBtn.classList.remove('clicked');
    });

    clickedBtn.classList.add('clicked');
  });
  // 우리칭찬왕 버튼 클릭시 CSS 추가 끝 - 240219

}


if (myTokenPage) {
  // 마이프로필 자동 퍼센트 계산 시작 - 240220
  const timePercent = doc.querySelector('#remainTimeBar');
  const now = new Date();
  const nowDate = new Date().getDate();
  const lastDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const remainDate = Math.floor((nowDate / lastDate) * 100);
  console.log(remainDate);

  timePercent.querySelector('.progress-bar').style.width = remainDate + '%';
  timePercent.querySelector('.progress-bar').innerHTML = remainDate + '%';
  // 마이프로필 자동 퍼센트 계산 끝 - 240220

  // 마이프로필 버튼 클릭시 CSS 추가 시작 - 240220
  const myTokenBtn = doc.querySelectorAll('.myTokenBtn button');
  const myTokenList = doc.querySelectorAll('.myTokenList');
  myTokenBtn.forEach((btn, btnIndex) => {
    btn.addEventListener('click', () => {

      myTokenBtn.forEach((siblingBtn, siblingIndex) => {
        siblingBtn.classList.remove('clicked');
        myTokenList[siblingIndex].style.display = 'none';
      });

      btn.classList.add('clicked');
      myTokenList[btnIndex].style.display = 'flex';
    });
  });
  // 마이프로필 버튼 클릭시 CSS 추가 끝 - 240219
}

const footer = doc.querySelector('#footer');
if (footer) {
  footer.innerHTML =
    `<div class="footer w-100 text-center fw-med fs-6" style="color:#418dd4;">ⓒ 2024, made 땡큐토큰</div>`;
}