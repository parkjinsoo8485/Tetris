# 테트리스 게임 (Tetris Game)

파이썬과 pygame을 사용한 테트리스 게임입니다.

## 기능

- 기본 테트리스 게임플레이
- 점수 시스템
- 효과음 지원 (블록 착지, 줄 삭제, 게임 오버)
- 다음 블록 미리보기

## 실행 방법

1. 필요한 패키지 설치:
   ```bash
   pip install pygame
   ```

2. 게임 실행:
   ```bash
   python tetris.py
   ```
   
   또는 PowerShell에서:
   ```powershell
   .\run_game.ps1
   ```

## 조작 방법

- **← → ↓**: 블록 이동
- **SPACE**: 블록 회전
- **ESC**: 게임 종료

## 파일 구조

- `tetris.py`: 메인 게임 파일
- `score_system.py`: 점수 시스템
- `sounds/`: 효과음 파일
- `assets/blocks/`: 블록 이미지 파일
- `run_game.ps1`: PowerShell 실행 스크립트

## 요구사항

- Python 3.11+
- pygame 2.6.1+

## 라이선스

이 프로젝트는 자유롭게 사용 가능합니다.

