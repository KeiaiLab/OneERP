// commitlint.config.js — 글로벌 ai-dev/templates/commitlint.config.js 사본.
// Conventional Commits + 한국어 본문 허용.
// 자동화 루프 우회: 커밋 메시지에 '[skip-hooks]' 트레일러 (ralph-loop 등).

module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'style', 'refactor', 'test', 'chore', 'ci', 'build', 'perf', 'revert'],
    ],
    'subject-case': [0],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'header-max-length': [2, 'always', 100],
    'body-max-line-length': [0],
    'body-leading-blank': [1, 'always'],
    'footer-leading-blank': [1, 'always'],
    'type-empty': [2, 'never'],
    'type-case': [2, 'always', 'lower-case'],
    'scope-case': [2, 'always', 'lower-case'],
  },
  ignores: [
    (msg) => msg.includes('[skip-hooks]'),
    (msg) => /^Merge (branch|pull request)/.test(msg),
    (msg) => /^Revert "/.test(msg),
  ],
};
