/** @type {import('ts-jest').JestConfigWithTsJest} */
module.exports = {
  testEnvironment: 'jsdom',
  testMatch: ['<rootDir>/src/**/__tests__/**/*.(test|spec).(ts|tsx|js|jsx)'],
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: 'tsconfig.json' }],
  },
  moduleNameMapper: {
    '^.*services/api(\\.ts)?$': '<rootDir>/src/__mocks__/api.ts',
    '\\.(css|less|scss)$': 'identity-obj-proxy',
    '\\.(png|jpg|svg)$': '<rootDir>/src/__mocks__/fileMock.js',
  },
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.tsx'],
  transformIgnorePatterns: ['node_modules/(?!(.*\\.mjs$|.*\\.esm\\.js$))'],
};
