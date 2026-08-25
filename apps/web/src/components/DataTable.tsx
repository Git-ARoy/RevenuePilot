'use client';

import React from 'react';

export interface Column<T> {
  header: string;
  accessorKey?: keyof T;
  cell?: (item: T) => React.ReactNode;
  className?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  loading?: boolean;
  onRowClick?: (item: T) => void;
  emptyMessage?: string;
}

export default function DataTable<T extends { id?: string | number }>({
  columns,
  data,
  loading = false,
  onRowClick,
  emptyMessage = 'No records found',
}: DataTableProps<T>) {
  if (loading) {
    return (
      <div className="bg-white border border-[#E5E5E5] rounded-xl overflow-hidden shadow-xs">
        <div className="p-4 space-y-3">
          <div className="h-4 bg-[#F5F5F4] rounded w-full animate-pulse"></div>
          <div className="h-10 bg-[#FAFAF9] rounded w-full animate-pulse"></div>
          <div className="h-10 bg-[#FAFAF9] rounded w-full animate-pulse"></div>
          <div className="h-10 bg-[#FAFAF9] rounded w-full animate-pulse"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-[#E5E5E5] rounded-xl overflow-hidden shadow-xs">
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[#E5E5E5] bg-[#FAFAF9]">
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className={`py-3 px-4 text-[11px] font-semibold uppercase tracking-wider text-[#737373] ${
                    col.className || ''
                  }`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F0F0F0]">
            {data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="py-12 text-center text-[#737373] text-xs font-medium"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((item, rowIdx) => (
                <tr
                  key={item.id ? String(item.id) : rowIdx}
                  onClick={() => onRowClick && onRowClick(item)}
                  className={`transition-colors ${
                    onRowClick ? 'cursor-pointer hover:bg-[#F9FAFB]' : ''
                  }`}
                >
                  {columns.map((col, colIdx) => (
                    <td key={colIdx} className={`py-3.5 px-4 text-[#171717] ${col.className || ''}`}>
                      {col.cell
                        ? col.cell(item)
                        : col.accessorKey
                        ? String(item[col.accessorKey] ?? '-')
                        : null}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
