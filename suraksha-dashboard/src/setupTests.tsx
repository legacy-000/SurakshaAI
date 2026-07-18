import '@testing-library/jest-dom';

const { TextEncoder, TextDecoder } = require('util');
Object.assign(global, { TextEncoder, TextDecoder });

global.fetch = jest.fn();

// ponytail: jsdom lacks scrollIntoView, which ChatPage calls in useEffect
Element.prototype.scrollIntoView = jest.fn();

jest.mock('recharts', () => {
  const Div = ({ children }: any) => (children ? <div>{children}</div> : <div />);
  return {
    ResponsiveContainer: Div,
    BarChart: Div,
    Bar: () => <div />,
    XAxis: () => <div />,
    YAxis: () => <div />,
    Tooltip: () => <div />,
    CartesianGrid: () => <div />,
    LineChart: Div,
    Line: () => <div />,
    PieChart: Div,
    Pie: () => <div />,
    Cell: () => <div />,
    Legend: () => <div />,
    AreaChart: Div,
    Area: () => <div />,
    ComposedChart: Div,
    ReferenceLine: () => <div />,
    ScatterChart: Div,
    Scatter: () => <div />,
    ZAxis: () => <div />,
    LabelList: () => <div />,
  };
});

// ponytail: react-leaflet not installed in this project; pages use leaflet directly
// jest.mock('react-leaflet', () => ({
//   MapContainer: ({ children }: any) => <div>{children}</div>,
//   ... etc
// }));

jest.mock('lucide-react', () => {
  const Icon = () => <div>icon</div>;
  return new Proxy({}, { get: () => Icon });
});

jest.mock('vis-network/standalone', () => ({ Network: jest.fn() }));
jest.mock('vis-data', () => ({ DataSet: jest.fn(), DataView: jest.fn() }));
jest.mock('html2canvas', () => jest.fn().mockResolvedValue({ toDataURL: () => '', width: 100, height: 100 }));
jest.mock('jspdf', () => {
  const MockJsPDF = jest.fn().mockImplementation(() => ({
    addImage: jest.fn().mockReturnThis(),
    save: jest.fn().mockReturnThis(),
    addPage: jest.fn().mockReturnThis(),
    setFontSize: jest.fn().mockReturnThis(),
    text: jest.fn().mockReturnThis(),
    internal: { pageSize: { getWidth: () => 210, getHeight: () => 297 } },
  }));
  return { jsPDF: MockJsPDF };
});
