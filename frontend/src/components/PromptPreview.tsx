interface Props {
  prompt: string;
  onClose: () => void;
}

export default function PromptPreview({ prompt, onClose }: Props) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-[600px] max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h3 className="font-medium text-gray-800">System Prompt Preview</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-lg"
          >
            x
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          <pre className="text-sm font-mono whitespace-pre-wrap text-gray-700">
            {prompt}
          </pre>
        </div>
      </div>
    </div>
  );
}
