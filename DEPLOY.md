# 배포 (GitHub Pages)

GitHub 웹 UI의 **드래그 업로드는 1회당 100개**까지만 됩니다. `img/` 폴더는 294개라 웹으로는 안 올라갑니다.
git 명령어를 쓰면 제한이 없습니다.

## 준비

`git --version`이 동작하면 넘어가고, 아니면 <https://git-scm.com/download/win> 에서 설치하세요.
(설치할 때 기본 옵션 그대로 두면 Windows용 인증 도우미가 같이 깔려서, 첫 push 때 브라우저로 로그인하면 끝입니다.)

---

## 방법 A — 빠진 `img/`만 추가 (권장)

이미 웹으로 올린 파일은 그대로 두고 이미지만 얹습니다. 히스토리가 보존되고 안전합니다.

PowerShell에서:

```powershell
cd C:\Users\user\Downloads
git clone https://github.com/3r15/my-study.git
Copy-Item -Recurse -Force "산업기사필기\study-site\img" "my-study\img"
cd my-study
git add img
git commit -m "이미지 294개 추가"
git push
```

첫 push에서 브라우저 로그인 창이 뜨면 GitHub 계정으로 승인하면 됩니다.

> 앞으로 파일을 고칠 때는 `my-study` 폴더에서 작업하고
> `git add . && git commit -m "설명" && git push` 세 줄이면 끝입니다.

---

## 방법 B — 로컬 폴더 전체를 원본으로 덮어쓰기

`study-site` 폴더가 최신이고 원격을 여기에 맞추고 싶을 때. **원격 히스토리가 지워집니다.**

```powershell
cd C:\Users\user\Downloads\산업기사필기\study-site
git init
git branch -M main
git remote add origin https://github.com/3r15/my-study.git
git add .
git commit -m "학습 사이트 전체"
git push -f origin main
```

---

## GitHub Pages 켜기

레포 → **Settings → Pages** → Source: `Deploy from a branch` → Branch: `main` / `/ (root)` → Save

1~2분 뒤 <https://3r15.github.io/my-study/> 에서 열립니다.

## 올린 뒤 확인

1. `https://github.com/3r15/my-study/tree/main/img` 에 파일이 294개인지
2. 사이트에서 **핵심요약 → 아무 항목 → "요약집 원본 보기"** 를 눌러 이미지가 뜨는지
3. **기출문제 → 2025년 2회 → 50번**(트리 그림 문항)이 제대로 보이는지

이미지가 깨져 보이면 브라우저에서 `Ctrl+Shift+R`로 강력 새로고침 하세요. 서비스 워커가 예전 응답을 캐시하고 있을 수 있습니다.

## 데이터를 바꿔서 다시 올릴 때

`sw.js` 안의 버전을 올려야 사용자 브라우저의 옛 캐시가 비워집니다.

```js
const V = 'jbsg-v1';   →   const V = 'jbsg-v2';
```

## 참고 — 용량

전체 2.8MB (이미지 2.1MB, 데이터 0.6MB). GitHub 제한(파일당 100MB, 레포 권장 1GB)에 한참 못 미칩니다.
